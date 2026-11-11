from pathlib import Path
import json,io
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from PIL import Image

WORK=Path(__file__).resolve().parents[1];OLD=WORK/'reference'
V=['NJFU 895','HENAN ZL','LIAON LHY','LIAON MZHY','LIAON XQY','SHANXI QZ','SHANXI XY']
T=['895','ZL','LHY','MZHY','XQY','QZ','XY']
PALETTE=['#2878A5','#67A9A0','#8D78A8','#C59649','#C66C75','#7D9C55','#8B6C56'];COL=dict(zip(V,PALETTE))
D=pd.read_csv(WORK/'data/seed_features.csv');MODEL=['Morphology','Color','Texture','Combined']
MC=['#7D9C55','#C59649','#8D78A8','#2878A5']
E=pd.read_csv(WORK/'tables/cluster_rank_effects.csv').set_index('trait');MET=pd.read_csv(WORK/'tables/primary_and_ablation_metrics.csv')
STYLE={'font.family':'Times New Roman','font.size':11,'axes.labelsize':12,'axes.titlesize':12,'xtick.labelsize':11,'ytick.labelsize':11,'legend.fontsize':10.5,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'grid.linewidth':.45,'grid.alpha':.2,'figure.facecolor':'white','savefig.facecolor':'white','mathtext.fontset':'stix'}
plt.rcParams.update(STYLE)
PREVIEW=WORK/'audit/figure_preview';PREVIEW.mkdir(exist_ok=True)
manifest=[]
def save(fig,number,caption,sources):
 name=f'Figure_{number:02d}'
 buf=io.BytesIO();fig.savefig(buf,format='tiff',dpi=600);buf.seek(0)
 with Image.open(buf) as im:im.convert('RGB').save(WORK/'figures'/f'{name}.tiff',compression='tiff_lzw',dpi=(600,600))
 fig.savefig(PREVIEW/f'{name}.png',dpi=160)
 manifest.append({'figure':number,'file':f'{name}.tiff','caption':caption,'sources':sources,'font':'Times New Roman','dpi':600,'width_in':fig.get_figwidth(),'height_in':fig.get_figheight()})
 plt.close(fig);print('Rendered',name,flush=True)

def distributions(number,traits,labels):
 fig,axes=plt.subplots(2,2,figsize=(7.2,5.8));fig.subplots_adjust(left=.10,right=.985,bottom=.145,top=.98,wspace=.27,hspace=.25)
 rng=np.random.default_rng(42)
 for ax,trait,label in zip(axes.flat,traits,labels):
  samples=[D.loc[D.variety==v,trait].to_numpy() for v in V]
  violin=ax.violinplot(samples,positions=np.arange(7),widths=.8,showextrema=False,bw_method=.28)
  for body,color in zip(violin['bodies'],PALETTE):body.set_facecolor(color);body.set_edgecolor(color);body.set_alpha(.18)
  for i,(v,values,color) in enumerate(zip(V,samples,PALETTE)):
   ax.scatter(i+rng.uniform(-.16,.16,len(values)),values,s=2.5,alpha=.14,color=color,linewidths=0)
   q=np.quantile(values,[.25,.5,.75]);ax.plot([i,i],q[[0,2]],color='#243740',lw=2.5,zorder=3)
   ax.scatter(i,q[1],s=25,color='white',edgecolor='#243740',lw=.8,zorder=4)
   means=D[D.variety==v].groupby('batch')[trait].mean().to_numpy()
   ax.scatter(i+np.linspace(-.23,.23,len(means)) if len(means)>1 else [i+.21],means,marker='D',s=26,facecolors=color,edgecolors='white',linewidths=.6,zorder=5)
  ax.set_xticks(range(7),T,rotation=30,ha='right');ax.set_ylabel(label);ax.grid(axis='y');ax.set_axisbelow(True)
 fig.legend(handles=[Line2D([],[],marker='o',markeredgecolor='#243740',markerfacecolor='white',color='none',label='Median and IQR'),Line2D([],[],marker='D',markerfacecolor='#596B75',color='none',label='Acquisition-batch mean')],loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.52,.015))
 save(fig,number,'Individual-image distributions, medians and interquartile ranges, with acquisition-batch means.',['data/seed_features.csv'])

def hsv_histograms():
 fig,axes=plt.subplots(1,3,figsize=(7.2,3.6));fig.subplots_adjust(left=.08,right=.985,bottom=.26,top=.96,wspace=.29)
 rng=np.random.default_rng(20261113)
 for v in V:
  d=D[D.variety==v].reset_index(drop=True);clusters=[g.index.to_numpy() for _,g in d.groupby('batch')]
  cols=[f'{p}_hist_{j:02d}' for p,bins in [('h',18),('s',16),('v',16)] for j in range(bins)]
  xx=d[cols].to_numpy();bs=np.empty((2000,len(cols)))
  for b in range(2000):
   idx=[]
   for c in rng.integers(0,len(clusters),size=len(clusters)):
    ids=clusters[c];idx.extend(rng.choice(ids,len(ids),replace=True))
   bs[b]=xx[idx].mean(axis=0)
  lo,hi=np.quantile(bs,[.025,.975],axis=0);mean=xx.mean(axis=0);off=0
  for ax,bins,maximum in zip(axes,[18,16,16],[360,1,1]):
   xs=(np.arange(bins)+.5)*maximum/bins
   ax.plot(xs,mean[off:off+bins],color=COL[v],lw=1.5,label=v)
   ax.fill_between(xs,lo[off:off+bins],hi[off:off+bins],color=COL[v],alpha=.11,lw=0)
   off+=bins
 for ax,label,xlim in zip(axes,['Hue (degrees)','Saturation','Value'],[(0,360),(0,1),(0,1)]):ax.set_xlabel(label);ax.set_xlim(xlim);ax.set_ylim(bottom=0);ax.grid(axis='y')
 axes[0].set_ylabel('Mean pixel frequency');axes[0].set_xticks([0,120,240,360])
 fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=4,frameon=False,bbox_to_anchor=(.52,.005),fontsize=10)
 save(fig,8,'Mean HSV histograms with 95% two-stage batch/seed resampling bands, conditional on singleton batches.',['data/seed_features.csv'])

def effect_sizes():
 groups=[('Morphology',MC[0],['length_mm','width_mm','area_mm2','circularity'],['Length','Width','Area','Circularity']),('Color',MC[1],['s_mean','s_sd','v_mean','v_sd'],['Saturation mean','Saturation SD','Value mean','Value SD']),('Texture',MC[2],['glcm_contrast_d1','glcm_homogeneity_d1','glcm_correlation_d1','glcm_entropy_d1'],['Contrast','Homogeneity','Correlation','Entropy'])]
 fig,axes=plt.subplots(3,1,figsize=(7.2,6.0),sharex=True);fig.subplots_adjust(left=.24,right=.98,bottom=.10,top=.95,hspace=.48)
 for ax,(name,color,traits,labels) in zip(axes,groups):
  for i,t in enumerate(traits):
   r=E.loc[t];a,b=r.cluster_low_seven,r.cluster_high_seven;x=r.rank_effect_seven
   ax.plot([a,b],[i,i],color=color,lw=2.6);ax.plot([a,a,b,b],[i-.09,i+.09,i+.09,i-.09],color=color,lw=0) if False else None
   ax.scatter(x,i,s=45,color=color,edgecolor='white',lw=.6,zorder=3)
   ax.text(min(.94,b+.035),i,f'{x:.3f}',va='center',fontsize=11)
  ax.set_yticks(range(4),labels);ax.set_ylim(3.5,-.5);ax.set_xlim(0,1);ax.set_title(name,color=color,fontweight='bold',pad=7);ax.grid(axis='x');ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0)
 axes[-1].set_xlabel('Descriptive rank effect');save(fig,11,'Rank effects with 95% batch/seed resampling sensitivity intervals.',['tables/cluster_rank_effects.csv'])

def comparison():
 fig,axes=plt.subplots(1,2,figsize=(7.2,4.1));fig.subplots_adjust(left=.09,right=.985,bottom=.25,top=.95,wspace=.25)
 for ax,metric,ylabel in zip(axes,['accuracy','macro_f1'],['Accuracy (%)','Macro-F1 (%)']):
  for i,(name,color) in enumerate(zip(MODEL,MC)):
   r=MET[(MET.representation==name)&(MET.setting=='Fixed')].iloc[0];t=MET[(MET.representation==name)&(MET.setting=='Tuned')].iloc[0]
   value=100*r[metric];rgb=np.array(to_rgb(color));cm=LinearSegmentedColormap.from_list('soft',[1-(1-rgb)*.25,rgb])
   ax.imshow(np.linspace(0,1,256)[:,None],extent=(i-.29,i+.29,0,value),origin='lower',cmap=cm,aspect='auto',zorder=2)
   ax.bar(i,value,width=.58,facecolor='none',edgecolor=color,lw=.8,zorder=3)
   lo=r[metric+'_cluster_low']*100;hi=r[metric+'_cluster_high']*100
   ax.errorbar(i,value,yerr=np.array([[value-lo],[hi-value]]),fmt='none',color='#243740',lw=1,capsize=3,zorder=4)
   ax.scatter(i,t[metric]*100,marker='D',s=32,color='#243740',zorder=5)
   ax.text(i,hi+3,f'{value:.2f}',ha='center',fontsize=10.5)
  ax.set_xticks(range(4),['Morph.','Color','Texture','All']);ax.set_ylim(0,104);ax.set_xlim(-.6,3.6);ax.set_ylabel(ylabel);ax.grid(axis='y');ax.set_axisbelow(True)
 fig.legend(handles=[Line2D([],[],marker='s',color='none',markerfacecolor='#9AABB4',label='Fixed parameters'),Line2D([],[],marker='D',color='none',markerfacecolor='#243740',label='Training-only tuning')],ncol=2,loc='lower center',frameon=False,bbox_to_anchor=(.52,.035))
 save(fig,13,'Fixed-model performance with cluster-resampling intervals and training-only tuned estimates.',['tables/primary_and_ablation_metrics.csv'])

def confusion():
 pred=pd.read_csv(WORK/'data/primary_predictions.csv');fig,axes=plt.subplots(2,2,figsize=(7.2,7.4));fig.subplots_adjust(left=.105,right=.88,top=.95,bottom=.14,wspace=.25,hspace=.42)
 from sklearn.metrics import confusion_matrix
 cm=LinearSegmentedColormap.from_list('teal',['#F5F8F7','#B3D6D2','#4A989E','#185A70'])
 for ax,name in zip(axes.flat,MODEL):
  p=pred[(pred.setting=='Fixed')&(pred.representation==name)];counts=confusion_matrix(p.variety,p.prediction,labels=V);pct=counts/counts.sum(axis=1,keepdims=True)*100
  im=ax.imshow(pct,cmap=cm,vmin=0,vmax=100)
  for i in range(7):
   ax.add_patch(Rectangle((i-.5,i-.5),1,1,fill=False,edgecolor='#3B5159',lw=.65))
   for j in range(7):
    if counts[i,j]:ax.text(j,i,str(counts[i,j]),ha='center',va='center',fontsize=11.5,color='white' if pct[i,j]>60 else '#243740')
  ax.set_xticks(range(7),T,rotation=40,ha='right');ax.set_yticks(range(7),T);ax.tick_params(length=0);ax.set_title(name,fontweight='bold',pad=9)
  for spine in ax.spines.values():spine.set_visible(False)
 cax=fig.add_axes([.91,.16,.018,.70]);cb=fig.colorbar(im,cax=cax);cb.set_label('Within-material row (%)',fontsize=11)
 fig.supxlabel('Predicted material',y=.035,fontsize=12);fig.supylabel('Observed material',x=.015,fontsize=12)
 save(fig,14,'Confusion matrices. Numbers are image counts; color indicates within-row percentages. Blank cells are zero.',['data/primary_predictions.csv'])

def contributions():
 delta=pd.read_csv(WORK/'tables/paired_representation_differences.csv');imp=pd.read_csv(WORK/'tables/block_permutation_summary.csv').set_index('feature_group')
 fig,axes=plt.subplots(1,2,figsize=(7.2,4.2),gridspec_kw={'width_ratios':[1.2,1]});fig.subplots_adjust(left=.21,right=.985,top=.86,bottom=.26,wspace=.36)
 for i,(group,color,n) in enumerate(zip(MODEL[:3],MC[:3],[81,35,68])):
  for setting,offset,marker in [('Fixed',-.10,'o'),('Tuned',.10,'D')]:
   r=delta[(delta.setting==setting)&(delta.removed_group==group)].iloc[0]
   x=-r.macro_f1_difference*100;lo=-r.macro_f1_high*100;hi=-r.macro_f1_low*100
   axes[0].errorbar(x,i+offset,xerr=np.array([[x-lo],[hi-x]]),fmt=marker,color=color,markerfacecolor=color if setting=='Fixed' else 'white',ms=6,capsize=2.5,lw=1.4)
  r=imp.loc[group];axes[1].errorbar(r['mean']*100,i,xerr=r['std']*100,fmt='o',color=color,ms=7,capsize=4,lw=2)
  axes[1].text(r['mean']*100,i-.24,f"{r['mean']*100:.2f}",ha='center',fontsize=11)
 axes[0].axvline(0,color='#788A91',lw=.9,ls='--');axes[0].set_yticks(range(3),['Remove morphology\n81 descriptors','Remove color\n35 descriptors','Remove texture\n68 descriptors'],fontsize=10.5);axes[0].set_xlim(-19,7)
 axes[0].set_xlabel('Macro-F1 change after removal\n(percentage points)',fontsize=11);axes[0].set_title('Retraining ablation',fontweight='bold')
 axes[1].set_yticks(range(3),[]);axes[1].set_xlim(0,62);axes[1].set_xlabel('Macro-F1 loss under permutation\n(percentage points)',fontsize=11);axes[1].set_title('Perturbation sensitivity',fontweight='bold')
 for ax in axes:ax.set_ylim(2.5,-.5);ax.grid(axis='x');ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0)
 fig.legend(handles=[Line2D([],[],marker='o',color='#4C6069',label='Fixed parameters'),Line2D([],[],marker='D',markerfacecolor='white',color='#4C6069',label='Training-only tuning')],loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.52,.02))
 save(fig,15,'Retraining ablation with paired batch-resampling intervals, and 1000-permutation sensitivity with mean ± SD.',['tables/paired_representation_differences.csv','tables/block_permutation_summary.csv'])

def batch_outcomes():
 contexts=pd.read_csv(WORK/'data/batch_context_predictions.csv.gz');ctx=pd.read_csv(WORK/'tables/batch_validation_reproduced.csv')
 unseen=pd.read_csv(WORK/'tables/ten_held_batch_outcomes.csv');unseen=unseen[unseen.model=='Combined'].copy()
 controls=contexts[(contexts.model=='Combined')&(contexts.validation=='Matched seed split')].groupby(['split','variety']).correct.mean()
 out=[]
 for r in unseen.itertuples():
  cc=ctx[(ctx.model=='Combined')&(ctx.validation=='Unseen batch')];split_ids=cc[cc.held_batches.str.split('|').map(lambda a:r.held_batch in a)].split
  vals=np.array([controls.loc[(i,r.material)] for i in split_ids]);out.append({**r._asdict(),'matched_mean':vals.mean(),'matched_min':vals.min(),'matched_max':vals.max()})
 tab=pd.DataFrame(out).drop(columns='Index');tab.to_csv(WORK/'tables/ten_batch_combined_with_controls.csv',index=False)
 fig,ax=plt.subplots(figsize=(7.2,5.4));fig.subplots_adjust(left=.21,right=.94,bottom=.16,top=.98)
 for i,r in enumerate(tab.itertuples()):
  color=COL[r.material]
  ax.plot([r.mean_recall*100,r.matched_mean*100],[i,i],color=color,alpha=.35,lw=1)
  ax.errorbar(r.mean_recall*100,i-.1,xerr=np.array([[(r.mean_recall-r.context_min)*100],[(r.context_max-r.mean_recall)*100]]),fmt='^',color=color,ms=7,capsize=2,lw=1.7)
  ax.errorbar(r.matched_mean*100,i+.1,xerr=np.array([[(r.matched_mean-r.matched_min)*100],[(r.matched_max-r.matched_mean)*100]]),fmt='o',markerfacecolor='white',color=color,ms=6,capsize=2,lw=1.2)
 ax.set_yticks(range(len(tab)),[r.held_batch.split(' ',1)[1] for r in tab.itertuples()]);ax.set_ylim(len(tab)-.5,-.5);ax.set_xlim(0,103);ax.set_xticks(range(0,101,20));ax.set_xlabel('Material-specific recall (%)');ax.grid(axis='x');ax.tick_params(axis='y',length=0);ax.spines['left'].set_visible(False)
 fig.legend(handles=[Line2D([],[],marker='^',color='#536973',label='Held-out batch'),Line2D([],[],marker='o',markerfacecolor='white',color='#536973',label='Matched random control')],loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.53,.015))
 save(fig,16,'Ten held-out-batch outcomes for the combined model. Symbols show means and bars ranges across overlapping training contexts.',['tables/ten_batch_combined_with_controls.csv'])

def main():
 (WORK/'figures').mkdir(exist_ok=True)
 distributions(6,['length_mm','width_mm','area_mm2','circularity'],['Length (mm)','Width (mm)','Area (mm²)','Circularity'])
 distributions(7,['h_circ_mean_deg','s_mean','v_mean','v_sd'],['Circular mean hue (°)','Mean saturation','Mean value','Within-image value SD'])
 distributions(10,['glcm_contrast_d1','glcm_homogeneity_d1','glcm_correlation_d1','glcm_entropy_d1'],['Contrast (d = 1)','Homogeneity (d = 1)','Correlation (d = 1)','Entropy (bits, d = 1)'])
 hsv_histograms();effect_sizes();comparison();confusion();contributions();batch_outcomes()
 (WORK/'figures/figure_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if __name__=='__main__':main()
