from lab.evidence import student_seed
from lab.navigation import set_stage
from lab.ui import text_response
from simulation.plotting import sample_figure
from simulation.sensors import SensorConfig,sample_metrics,static_samples
from simulation.filters import moving_average,median_filter

TITLES=('Sensor errors: evidence, not certainty','Filter outputs: smoothing and outliers','Fusion: combining imperfect evidence','Delay and decisions: consequences of estimates')

def render(st):
    index=st.session_state['walkthrough_index'];st.header(f'Walkthrough {index+1} — {TITLES[index]}')
    if index==0:
        st.write('Noise scatters readings; bias shifts their center; quantization rounds them; dropout means no reading. An outlier can pull a mean far from the typical value. More samples do not remove systematic bias.')
        a,b,c=st.columns(3)
        noise=a.slider('Noise σ (m)',0.,.4,.08,.01);bias=b.slider('Bias (m)',-.4,.4,0.,.01)
        resolution=c.select_slider('Resolution (m)',options=[.001,.01,.05,.1,.25],value=.01)
        dropout=a.slider('Dropout probability',0.,.4,.02,.01);outliers=b.slider('Outlier probability',0.,.25,.02,.01)
        false_detection=c.slider('False-detection probability',0.,.2,0.,.01)
        values=static_samples(2.,180,SensorConfig(noise_std=noise,bias=bias,resolution=resolution,dropout_rate=dropout,outlier_rate=outliers,outlier_scale=1.2,false_detection_rate=false_detection),student_seed(st.session_state['student']['course_id'],'playground'))
        figure=sample_figure(values,2.);st.pyplot(figure)
        import matplotlib.pyplot as plt
        plt.close(figure)
        st.dataframe([sample_metrics(values,2.)],hide_index=True)
        text_response(st,'concepts.observation','What changed when you increased noise versus bias? Refer to the plot and statistics.')
        st.info('Next: how can we reduce scattering without assuming every reading is correct?')
    elif index==1:
        st.write('A moving average replaces a reading with the mean of the last N valid readings. Larger N often smooths noise but can lag after a change. Missing readings are omitted, not treated as zero; the prior estimate is held until new evidence arrives.')
        st.latex(r'\hat d_k=\frac{1}{N}\sum_{i=0}^{N-1}d_{k-i}')
        st.write('For [2.0, 2.1, 8.0] m, the mean is 4.033 m and the median (middle sorted value) is 2.1 m. The median resists the isolated outlier. Neither filter automatically removes a constant sensor bias.')
        window=st.slider('Example window (valid readings)',1,5,3)
        values=[2.,2.1,8.,2.2,2.3]
        st.dataframe({'Reading (m)':values,'Moving average (m)':moving_average(values,window),'Median (m)':median_filter(values,window)})
        st.write('Exponential filtering uses a fraction α of the new measurement and retains 1−α of the prior estimate. Smaller α usually means more smoothing and more lag.')
        st.latex(r'\hat d_k=\alpha d_k+(1-\alpha)\hat d_{k-1}')
        st.info('Next: one sensor may be fast/noisy while another is slow/biased. Can we use both?')
    elif index==2:
        st.latex(r'\hat d=w\hat d_A+(1-w)\hat d_B')
        st.write('w is the weight on Sensor A, not a probability that A is correct. At w=0.25, A=1.8 m and B=2.4 m, the fused estimate is 0.25×1.8+0.75×2.4=2.25 m. If one estimate is unavailable, this lab uses the other; if both are unavailable, there is no estimate.')
        weight=st.slider('Example weight on A',0.,1.,.25,.05);st.metric('Fused distance',f'{weight*1.8+(1-weight)*2.4:.3f} m')
        st.write('Fusion can reduce random error, but two agreeing sensors may share a bias. A held value remains available computationally without being a fresh measurement.')
        st.info('Next: a clean estimate can still react too late to an approaching obstacle.')
    else:
        st.write('Mission 2 changes the true distance at 6.00 s. Response delay is the time until the estimate is within 0.15 m of the new distance for three consecutive samples (0.05 s apart). We report the confirmation time, not the first lucky crossing.')
        st.latex(r'\text{delay}=t_{\text{third consecutive acceptable sample}}-6.00\ \mathrm{s}')
        st.write('For acceptable samples at 6.30, 6.35 and 6.40 s, delay is 0.40 s. RMSE summarizes typical error; maximum error reveals peaks; availability measures whether an estimate exists, not whether it is fresh.')
        st.write('Mission 3 turns estimates into MOVE, SLOW, STOP or INSUFFICIENT EVIDENCE. Ground truth is visible for evaluation only: the rule uses sensor evidence. A false-safe MOVE and an unnecessary STOP affect people differently.')
        st.info('Next: independently characterize a sensor, then test estimation and decision choices with predictions and evidence.')
    if st.button('Mark reviewed',key='review.'+str(index)):
        st.session_state['reviewed_walkthroughs']=sorted(set(st.session_state['reviewed_walkthroughs'])|{index})
    a,b=st.columns(2)
    if a.button('Previous walkthrough',disabled=index==0): st.session_state['walkthrough_index']=index-1;set_stage(st,'concepts')
    if b.button('Next walkthrough',disabled=index==3 or index not in st.session_state['reviewed_walkthroughs']): st.session_state['walkthrough_index']=index+1;set_stage(st,'concepts')
    if index==3 and st.button('Continue to Mission 1',disabled=len(st.session_state['reviewed_walkthroughs'])<4,type='primary'): set_stage(st,'mission_1')
