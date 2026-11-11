"""Reproduce fixed benchmarks, then training-only tuning and leave-group-out refits.

Existing test seeds never enter scaling, fitting, or parameter selection. All
analyses after review are sensitivity analyses on the same prespecified split.
"""
from pathlib import Path
from itertools import product
from concurrent.futures import ThreadPoolExecutor
import json,time,hashlib
import numpy as np,pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV,StratifiedKFold,train_test_split
from sklearn.metrics import accuracy_score,balanced_accuracy_score,f1_score,confusion_matrix
from joblib import parallel_backend,dump
from threadpoolctl import threadpool_limits

WORK=Path(__file__).resolve().parents[1];OLD=WORK/'reference';SEED=42;B=2000;N_PERM=1000
GRID={'svc__C':[.1,1,10,50,100],'svc__gamma':[.0001,.001,.01,.1,1.,'scale']}
def model(C=50.,gamma='scale'):
 return Pipeline([('scaler',StandardScaler()),('svc',SVC(C=C,gamma=gamma,kernel='rbf',cache_size=256,random_state=SEED))])
def metrics(y,p,labels):
 cm=confusion_matrix(y,p,labels=labels);den=cm.sum(axis=0)+cm.sum(axis=1)
 return {'accuracy':float(np.mean(y==p)),'balanced_accuracy':float(np.mean(np.diag(cm)/cm.sum(axis=1))), 'macro_f1':float(np.mean(np.divide(2*np.diag(cm),den,out=np.zeros(len(labels)),where=den>0)))}

def run_fixed_cv(d,groups):
 """Reproduce the archived fixed-benchmark folds, distinct from tuning folds."""
 train,test=train_test_split(np.arange(len(d)),test_size=.2,random_state=SEED,stratify=d.batch)
 assert set(train)==set(np.flatnonzero(d.split.to_numpy()=='train'))
 archive=pd.read_csv(WORK/'data/training_cv_folds.csv').set_index('seed_id').validation_fold
 assert set(archive.index)==set(d.seed_id.iloc[train]) and not set(archive.index)&set(d.seed_id.iloc[test])
 folds=list(StratifiedKFold(5,shuffle=True,random_state=SEED).split(train,d.variety.iloc[train]))
 labels=sorted(d.variety.unique());y=pd.Categorical(d.variety,categories=labels).codes
 rows=[];predictions=[]
 for name,cols in groups.items():
  X=d[cols].to_numpy()
  for fold,(tr,va) in enumerate(folds,1):
   ti=train[tr];vi=train[va]
   assert set(d.seed_id.iloc[vi])==set(archive[archive==fold].index)
   fitted=model().fit(X[ti],y[ti]);pr=fitted.predict(X[vi])
   assert np.allclose(fitted.named_steps['scaler'].mean_,X[ti].mean(axis=0))
   rows.append({'model':name,'fold':fold,'training_n':len(ti),'validation_n':len(vi),**metrics(y[vi],pr,np.arange(len(labels)))})
   for index,pv in zip(vi,pr):predictions.append({'seed_id':d.seed_id.iloc[index],'fold':fold,'model':name,'variety':d.variety.iloc[index],'prediction':labels[pv],'correct':int(pv==y[index])})
 result=pd.DataFrame(rows);result.to_csv(WORK/'tables/fixed_training_cv_metrics.csv',index=False)
 pd.DataFrame(predictions).to_csv(WORK/'data/fixed_training_cv_predictions.csv',index=False)
 summary=result.groupby('model')[['accuracy','macro_f1','balanced_accuracy']].agg(['mean','std'])
 summary.to_csv(WORK/'tables/fixed_training_cv_summary.csv')
 return {'fold_manifest':'data/training_cv_folds.csv','tuning_fold_manifest_is_separate':True,'test_images_used':False,'fits':len(rows),'combined_accuracy_mean':float(summary.loc['Combined',('accuracy','mean')]),'combined_accuracy_sd':float(summary.loc['Combined',('accuracy','std')])}

def run_primary(d,groups):
 train=np.flatnonzero(d.split.to_numpy()=='train');test=np.flatnonzero(d.split.to_numpy()=='test')
 assert len(train)==1940 and len(test)==486 and not set(train)&set(test)
 labels=sorted(d.variety.unique());y=pd.Categorical(d.variety,categories=labels).codes;lab=np.arange(len(labels))
 sets=dict(groups)
 for name in ['Morphology','Color','Texture']:
  sets['Without '+name]=[c for c in groups['Combined'] if c not in groups[name]]
 (WORK/'data/analysis_feature_sets.json').write_text(json.dumps(sets,indent=2),encoding='utf-8')
 folds=list(StratifiedKFold(5,shuffle=True,random_state=SEED).split(train,y[train]))
 fm=[]
 for fold,(tr,va) in enumerate(folds,1):
  for i in va:fm.append({'seed_id':d.seed_id.iloc[train[i]],'selection_validation_fold':fold})
 pd.DataFrame(fm).to_csv(WORK/'data/tuning_cv_fold_manifest.csv',index=False)
 old=pd.read_csv(OLD/'tables/model_metrics.csv').set_index('model')
 records=[];predrows=[];preds={};fitted={};searches=[]
 (WORK/'models').mkdir(exist_ok=True)
 for name,cols in sets.items():
  X=d[cols].to_numpy();fixed=model().fit(X[train],y[train]);p=fixed.predict(X[test])
  rec={'representation':name,'setting':'Fixed','descriptors':len(cols),'C':50.,'gamma_spec':'scale','effective_gamma':fixed.named_steps['svc']._gamma,**metrics(y[test],p,lab)}
  if name in groups:
   for metric in ['accuracy','balanced_accuracy','macro_f1']:assert np.isclose(rec[metric],old.loc[name,metric],atol=1e-13),(name,metric)
  records.append(rec);preds[('Fixed',name)]=p;fitted[('Fixed',name)]=fixed
  gs=GridSearchCV(model(),GRID,scoring='f1_macro',cv=folds,n_jobs=8,refit=True,return_train_score=False,error_score='raise')
  with parallel_backend('threading'):gs.fit(X[train],y[train])
  tuned=gs.best_estimator_;pp=tuned.predict(X[test]);params=gs.best_params_
  rec={'representation':name,'setting':'Tuned','descriptors':len(cols),'C':params['svc__C'],'gamma_spec':str(params['svc__gamma']),'effective_gamma':tuned.named_steps['svc']._gamma,'selection_cv_macro_f1':gs.best_score_,**metrics(y[test],pp,lab)}
  records.append(rec);preds[('Tuned',name)]=pp;fitted[('Tuned',name)]=tuned
  for index,par in enumerate(gs.cv_results_['params']):
   r={'representation':name,'C':par['svc__C'],'gamma_spec':str(par['svc__gamma']),'mean_cv_macro_f1':gs.cv_results_['mean_test_score'][index],'sd_cv_macro_f1':gs.cv_results_['std_test_score'][index],'rank':int(gs.cv_results_['rank_test_score'][index])}
   for fold in range(5):r[f'fold_{fold+1}']=gs.cv_results_[f'split{fold}_test_score'][index]
   searches.append(r)
  for setting,pr,fit in [('Fixed',p,fixed),('Tuned',pp,tuned)]:
   for idx,pv in zip(test,pr):predrows.append({'seed_id':d.seed_id.iloc[idx],'variety':d.variety.iloc[idx],'batch':d.batch.iloc[idx],'representation':name,'setting':setting,'prediction':labels[pv],'correct':int(pv==y[idx])})
   dump({'pipeline':fit,'features':cols,'class_order':labels,'training_seed_ids':d.seed_id.iloc[train].tolist()},WORK/'models'/f"{setting.lower()}_{name.replace(' ','_').lower()}.joblib")
  print(name,'fixed/tuned accuracy',metrics(y[test],p,lab)['accuracy'],rec['accuracy'],flush=True)
 pd.DataFrame(searches).to_csv(WORK/'tables/training_grid_search.csv',index=False)
 pd.DataFrame(predrows).to_csv(WORK/'data/primary_predictions.csv',index=False)
 frame=d.iloc[test].reset_index(drop=True);byvar=[[g.index.to_numpy() for _,g in frame[frame.variety==v].groupby('batch')] for v in labels]
 rng=np.random.default_rng(20261112);boot={k:np.zeros((B,3)) for k in preds}
 for b in range(B):
  idx=[]
  for clusters in byvar:
   for c in rng.integers(0,len(clusters),size=len(clusters)):
    ids=clusters[c];idx.extend(rng.choice(ids,len(ids),replace=True))
  for k,p in preds.items():
   m=metrics(y[test][idx],p[idx],lab);boot[k][b]=[m['accuracy'],m['macro_f1'],m['balanced_accuracy']]
 for r in records:
  arr=boot[(r['setting'],r['representation'])]
  for j,met in enumerate(['accuracy','macro_f1','balanced_accuracy']):r[f'{met}_cluster_low'],r[f'{met}_cluster_high']=np.quantile(arr[:,j],[.025,.975])
 pd.DataFrame(records).to_csv(WORK/'tables/primary_and_ablation_metrics.csv',index=False)
 differences=[]
 for setting in ['Fixed','Tuned']:
  for name in sets:
   if name=='Combined':continue
   a=boot[(setting,'Combined')]-boot[(setting,name)]
   full=next(r for r in records if r['representation']=='Combined' and r['setting']==setting);reduced=next(r for r in records if r['representation']==name and r['setting']==setting)
   row={'setting':setting,'comparison':'Combined minus '+name,'removed_group':name.replace('Without ','') if name.startswith('Without ') else '', 'other_representation':name}
   for j,met in enumerate(['accuracy','macro_f1','balanced_accuracy']):
    row[met+'_difference']=full[met]-reduced[met];row[met+'_low'],row[met+'_high']=np.quantile(a[:,j],[.025,.975])
   differences.append(row)
 pd.DataFrame(differences).to_csv(WORK/'tables/paired_representation_differences.csv',index=False)
 rng=np.random.default_rng(43);cols=groups['Combined'];X=d.iloc[test][cols].to_numpy();fit=fitted[('Fixed','Combined')]
 baseline=metrics(y[test],preds[('Fixed','Combined')],lab)['macro_f1'];jobs=[]
 for name in ['Morphology','Color','Texture']:
  block=[cols.index(c) for c in groups[name]]
  for b in range(N_PERM):jobs.append((name,b,block,rng.permutation(len(test))))
 def permute(job):
  name,b,block,order=job;xp=X.copy();xp[:,block]=X[np.ix_(order,block)];pv=fit.predict(xp)
  return {'feature_group':name,'repeat':b,'macro_f1_drop':baseline-metrics(y[test],pv,lab)['macro_f1']}
 with ThreadPoolExecutor(max_workers=8) as pool:importance=list(pool.map(permute,jobs))
 im=pd.DataFrame(importance);im.to_csv(WORK/'tables/block_permutation_1000.csv',index=False)
 im.groupby('feature_group').macro_f1_drop.agg(['count','mean','std','min','max']).to_csv(WORK/'tables/block_permutation_summary.csv')
 majority=int(np.bincount(y[train]).argmax());p=np.full(len(test),majority)
 baseline_rows=[{'problem':'seven materials','evaluation':'fixed test','majority_material':labels[majority],'n':len(test),'accuracy':float(np.mean(y[test]==p)),'corpus_majority_fraction':float((y==majority).mean()),'training_n':len(train),'test_n':len(test)}]
 print('Primary bootstrap, ablation and permutation complete',flush=True)
 return baseline_rows

def run_batches(d,groups):
 counts=d.groupby('variety').batch.nunique();eligible=sorted(counts[counts>1].index)
 s=d[d.variety.isin(eligible)].reset_index(drop=True);y=pd.Categorical(s.variety,categories=eligible).codes;labels=np.arange(len(eligible))
 batches=[sorted(s.loc[s.variety==v,'batch'].unique()) for v in eligible];choices=list(product(*batches));assert len(choices)==32
 jobs=[(i,choice,name,cols) for i,choice in enumerate(choices) for name,cols in groups.items()]
 def job(spec):
  i,choice,name,cols=spec;X=s[cols].to_numpy();held=s.batch.isin(choice).to_numpy();tr=np.flatnonzero(~held);te=np.flatnonzero(held)
  assert not set(s.batch.iloc[tr])&set(s.batch.iloc[te])
  rng=np.random.default_rng(SEED+i);tr2=[];te2=[]
  for v in eligible:
   ids=np.flatnonzero(s.variety.to_numpy()==v);rng.shuffle(ids);n=int(np.sum(s.variety.iloc[te]==v));te2.extend(ids[:n]);tr2.extend(ids[n:])
  rows=[];pred=[];batchrows=[]
  for kind,tidx,eidx in [('Unseen batch',tr,te),('Matched seed split',np.asarray(tr2),np.asarray(te2))]:
   fit=model().fit(X[tidx],y[tidx]);p=fit.predict(X[eidx]);maj=int(np.bincount(y[tidx],minlength=4).argmax())
   rows.append({'model':name,'split':i,'validation':kind,'held_batches':'|'.join(choice),'train_n':len(tidx),'test_n':len(eidx),'majority_training_material':eligible[maj],'majority_test_accuracy':float(np.mean(y[eidx]==maj)),**metrics(y[eidx],p,labels)})
   for idx,pv in zip(eidx,p):pred.append({'split':i,'model':name,'validation':kind,'seed_id':s.seed_id.iloc[idx],'batch':s.batch.iloc[idx],'variety':s.variety.iloc[idx],'prediction':eligible[pv],'correct':int(pv==y[idx])})
   if kind=='Unseen batch':
    for b in choice:
     mask=s.batch.iloc[eidx].to_numpy()==b
     batchrows.append({'model':name,'split':i,'held_batch':b,'material':s.variety[s.batch==b].iloc[0],'unique_n':int(mask.sum()),'correct':int(np.sum(p[mask]==y[eidx][mask])),'recall':float(np.mean(p[mask]==y[eidx][mask]))})
  return rows,pred,batchrows
 rows=[];pred=[];batchrows=[]
 with ThreadPoolExecutor(max_workers=8) as pool:
  for i,result in enumerate(pool.map(job,jobs),1):
   a,b,c=result;rows.extend(a);pred.extend(b);batchrows.extend(c)
   if i%16==0:print('Cross-batch',i,'/',len(jobs),flush=True)
 m=pd.DataFrame(rows);m.to_csv(WORK/'tables/batch_validation_reproduced.csv',index=False)
 old=pd.read_csv(OLD/'tables/batch_validation.csv')
 compare=m.merge(old,on=['model','split','validation'],suffixes=('_new','_old'))
 for metric in ['accuracy','macro_f1','balanced_accuracy']:assert np.allclose(compare[metric+'_new'],compare[metric+'_old'],atol=1e-13)
 pd.DataFrame(pred).to_csv(WORK/'data/batch_context_predictions.csv.gz',index=False,compression='gzip')
 br=pd.DataFrame(batchrows);br.to_csv(WORK/'tables/batch_context_outcomes.csv',index=False)
 ag=br.groupby(['model','held_batch','material','unique_n']).recall.agg(['count','mean','std','min','max']).reset_index().rename(columns={'count':'training_contexts','mean':'mean_recall','std':'context_sd','min':'context_min','max':'context_max'})
 ag.to_csv(WORK/'tables/ten_held_batch_outcomes.csv',index=False)
 m.groupby(['model','validation'])[['accuracy','macro_f1','majority_test_accuracy']].agg(['mean','std','min','max']).to_csv(WORK/'tables/batch_validation_summary.csv')
 return {'four_materials':eligible,'unique_seeds':len(s),'unique_batches':int(s.batch.nunique()),'overlapping_combinations':len(choices),'four_class_corpus_majority_fraction':float(s.variety.value_counts().max()/len(s)),'all_original_scores_reproduced':True,'per_batch_values_are_context_averages_not_independent_runs':True}

def main():
 start=time.time();d=pd.read_csv(WORK/'data/seed_features.csv');groups=json.loads((WORK/'data/feature_groups.json').read_text())
 fixed_cv=run_fixed_cv(d,groups);base=run_primary(d,groups);batches=run_batches(d,groups)
 pd.DataFrame(base).to_csv(WORK/'tables/majority_baselines.csv',index=False)
 result={'passed':True,'grid':GRID,'selection_metric':'macro-F1','selection_folds':5,'scaling':'fit on each training fold only','holdout_unchanged':True,'test_never_used_for_selection':True,'bootstrap_samples':B,'permutations_per_group':N_PERM,'fixed_benchmark_cv':fixed_cv,'batch_results':batches,'wall_seconds':time.time()-start}
 (WORK/'audit/classification_analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':
 with threadpool_limits(limits=1):main()
