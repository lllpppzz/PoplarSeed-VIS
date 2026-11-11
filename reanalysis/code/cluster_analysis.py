"""Exploratory uncertainty with harvest-batch clusters, not biological replication."""
from pathlib import Path
import numpy as np,pandas as pd,json,time
from scipy import stats,optimize
from threadpoolctl import threadpool_limits

WORK=Path(__file__).resolve().parents[1];OLD=WORK/'reference'
SEED=20261111;B=2000
TRAITS=['length_mm','width_mm','area_mm2','perimeter_mm','aspect_ratio','circularity','compactness','solidity','eccentricity','roundness','equivalent_diameter_mm','s_mean','s_sd','v_mean','v_sd','h_circ_sd_deg','glcm_contrast_d1','glcm_dissimilarity_d1','glcm_homogeneity_d1','glcm_asm_d1','glcm_energy_d1','glcm_correlation_d1','glcm_entropy_d1','glcm_contrast_d2','glcm_dissimilarity_d2','glcm_homogeneity_d2','glcm_asm_d2','glcm_energy_d2','glcm_correlation_d2','glcm_entropy_d2']

def rank_effect(arrays):
 h=stats.kruskal(*arrays,axis=0).statistic
 n=sum(len(x) for x in arrays);k=len(arrays)
 return np.maximum(0,(h-k+1)/(n-k))

def random_intercept_reml(frame,trait):
 """Profile REML for y=material fixed mean + batch intercept + seed residual.
 Uses exact sufficient statistics for the full compound-symmetric covariance.
 The fixed effects are four material means, with no separate region term.
 """
 y=frame[trait].to_numpy();scale=y.std(ddof=1);center=y.mean()
 t=frame[['variety','batch']].copy();t['z']=(y-center)/scale
 g=t.groupby(['variety','batch']).z.agg(['mean','size','var']).reset_index()
 n=g['size'].to_numpy(float);m=g['mean'].to_numpy(float)
 wss=float(np.sum((n-1)*g['var'].to_numpy(float)))
 vc=pd.Categorical(g.variety).codes;k=len(np.unique(vc));N=len(y)
 def objective(lam,return_parts=False):
  den=1+n*lam;wt=n/den
  totals=np.bincount(vc,weights=wt,minlength=k)
  betas=np.bincount(vc,weights=wt*m,minlength=k)/totals
  q=wss+np.sum(wt*(m-betas[vc])**2)
  sig=q/(N-k)
  value=.5*((N-k)*np.log(sig)+np.log(den).sum()+np.log(totals).sum())
  return (value,sig,betas) if return_parts else value
 sol=optimize.minimize_scalar(lambda x:objective(np.exp(x)),bounds=(-18,18),method='bounded',options={'xatol':1e-10})
 lam=np.exp(sol.x)
 if objective(0)<=objective(lam)+1e-8:lam=0.
 _,sigma,_=objective(lam,True);tau=sigma*lam
 return {'trait':trait,'materials':k,'batches':len(g),'seeds':N,'batch_variance':tau*scale**2,'seed_residual_variance':sigma*scale**2,'batch_icc':tau/(tau+sigma),'variance_ratio':lam,'boundary_estimate':lam==0,'reml_optimized':bool(sol.success)}

def main():
 start=time.time();d=pd.read_csv(WORK/'data/seed_features.csv');varieties=sorted(d.variety.unique())
 byvar=[[(b,g.index.to_numpy()) for b,g in d[d.variety==v].groupby('batch')] for v in varieties]
 eligible=[i for i,x in enumerate(byvar) if len(x)>1];X=d[TRAITS].to_numpy()
 all_orig=[X[d.variety.to_numpy()==v] for v in varieties]
 orig7=rank_effect(all_orig);orig4=rank_effect([all_orig[i] for i in eligible])
 rng=np.random.default_rng(SEED)
 e7=np.zeros((B,len(TRAITS)));e4=e7.copy();means=np.zeros((B,len(varieties),len(TRAITS)))
 # Archive the resampling plan as image IDs and multiplicities only if needed for reproduction;
 # the RNG seed + fixed manifest + algorithm fully determine all resamples.
 for b in range(B):
  arrays=[]
  for v,clusters in enumerate(byvar):
   chosen=rng.integers(0,len(clusters),size=len(clusters));idx=[]
   for c in chosen:
    original=clusters[c][1];idx.extend(rng.choice(original,size=len(original),replace=True))
   arrays.append(X[idx]);means[b,v]=arrays[-1].mean(axis=0)
  e7[b]=rank_effect(arrays);e4[b]=rank_effect([arrays[i] for i in eligible])
  if (b+1)%250==0:print('Cluster bootstrap',b+1,'/',B,flush=True)
 np.savez_compressed(WORK/'data/cluster_bootstrap_draws.npz',effects_seven=e7,effects_four=e4,means=means,traits=np.array(TRAITS),varieties=np.array(varieties))
 old=pd.read_csv(OLD/'tables/kruskal_effects.csv').set_index('trait')
 rows=[]
 for j,t in enumerate(TRAITS):
  assert np.isclose(orig7[j],old.loc[t,'eta_squared_H'],rtol=1e-10)
  lo,hi=np.quantile(e7[:,j],[.025,.975]);l4,h4=np.quantile(e4[:,j],[.025,.975])
  rows.append({'trait':t,'rank_effect_seven':orig7[j],'cluster_low_seven':lo,'cluster_high_seven':hi,'old_seed_low_seven':old.loc[t,'effect_ci_low'],'old_seed_high_seven':old.loc[t,'effect_ci_high'],'rank_effect_four':orig4[j],'cluster_low_four':l4,'cluster_high_four':h4,'bootstrap_n':B,'seven_scope':'conditional on one observed batch for each LIAON material','four_scope':'10 harvest batches; biological independence not established'})
 pd.DataFrame(rows).to_csv(WORK/'tables/cluster_rank_effects.csv',index=False)
 combos=[('s_mean','LIAON LHY','SHANXI XY'),('v_mean','LIAON LHY','SHANXI XY'),('glcm_contrast_d1','LIAON LHY','LIAON MZHY'),('glcm_contrast_d1','LIAON LHY','LIAON XQY'),('glcm_contrast_d1','LIAON MZHY','LIAON XQY'),('glcm_contrast_d1','SHANXI QZ','SHANXI XY')]
 pairs=[]
 for t,a,b in combos:
  j=TRAITS.index(t);ia=varieties.index(a);ib=varieties.index(b);diff=means[:,ia,j]-means[:,ib,j]
  # Simultaneous conservative 95% familywise intervals for six specified contrasts via Bonferroni quantiles.
  lo,hi=np.quantile(diff,[.025/len(combos),1-.025/len(combos)])
  pairs.append({'trait':t,'material_a':a,'material_b':b,'batches_a':len(byvar[ia]),'batches_b':len(byvar[ib]),'mean_difference':all_orig[ia][:,j].mean()-all_orig[ib][:,j].mean(),'familywise_interval_low':lo,'familywise_interval_high':hi,'n_contrasts':len(combos),'equivalence_tested':False,'singleton_conditional':min(len(byvar[ia]),len(byvar[ib]))==1})
 pd.DataFrame(pairs).to_csv(WORK/'tables/cluster_pairwise_contrasts.csv',index=False)
 rep=d[d.variety.isin([varieties[i] for i in eligible])]
 comps=[random_intercept_reml(rep,t) for t in TRAITS]
 pd.DataFrame(comps).to_csv(WORK/'tables/batch_variance_reml.csv',index=False)
 per=[]
 for v,g in rep.groupby('variety'):
  for t in TRAITS:
   gg=g.groupby('batch')[t];ns=gg.size().to_numpy();ms=gg.mean().to_numpy();N=len(g);k=len(ns)
   mse=sum(((h[t]-h[t].mean())**2).sum() for _,h in g.groupby('batch'))/(N-k)
   msb=np.sum(ns*(ms-g[t].mean())**2)/(k-1);n0=(N-np.sum(ns**2)/N)/(k-1)
   raw=(msb-mse)/n0;tau=max(0,raw)
   per.append({'material':v,'trait':t,'batches':k,'seeds':N,'batch_var_mom':tau,'raw_batch_var_mom':raw,'within_batch_var':mse,'batch_icc_mom':tau/(tau+mse),'batch_mean_min':ms.min(),'batch_mean_max':ms.max()})
 pd.DataFrame(per).to_csv(WORK/'tables/batch_variance_by_material.csv',index=False)
 # Independent implementation check for a representative trait against statsmodels REML.
 import statsmodels.api as sm
 xx=pd.get_dummies(rep.variety,dtype=float);yy=rep.length_mm
 check=sm.MixedLM(yy,xx,groups=rep.batch).fit(reml=True,method='powell',disp=False)
 ours=comps[0];assert np.isclose(ours['batch_variance'],check.cov_re.iloc[0,0],rtol=.002,atol=1e-6)
 assert np.isclose(ours['seed_residual_variance'],check.scale,rtol=.002,atol=1e-6)
 result={'passed':True,'bootstrap_samples':B,'rng_seed':SEED,'all_seed_effects_reproduced':True,'reml_validated_against_statsmodels':True,'wall_seconds':time.time()-start,'warnings':['Each material occurs in one region; fixed effects represent material/source combinations.','Three materials have only one batch; all-material intervals condition on those batches.','Only 2–4 batches per replicated material; bootstrap intervals are sensitivity summaries, not robust population confidence bounds.','Harvest batches do not establish independent biological replication.']}
 (WORK/'audit/cluster_analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':
 with threadpool_limits(limits=1):main()
