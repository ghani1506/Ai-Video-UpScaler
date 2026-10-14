import os, shutil, subprocess, tempfile, json
from pathlib import Path
import streamlit as st

st.set_page_config(page_title='Clarity AI Video Upscaler', page_icon='🎞️', layout='centered')
st.title('🎞️ Clarity AI Video Upscaler')
st.caption('MP4 · AVI · 3GP → MP4 | Local processing on your Mac')

def binary(name, env=None):
    val = os.getenv(env, '') if env else ''
    for p in [val, shutil.which(name), str(Path.home()/'clarity-ai-engine'/name), str(Path.home()/'Desktop'/name)]:
        if p and Path(p).is_file() and os.access(p, os.X_OK): return str(Path(p).resolve())
    return None

def run(args, cwd=None):
    p = subprocess.run([str(x) for x in args], cwd=cwd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"Command: {' '.join(map(str,args))}\nExit code: {p.returncode}\n{p.stderr[-5000:]}\n{p.stdout[-1500:]}")
    return p.stdout

ffmpeg=binary('ffmpeg','FFMPEG_BIN'); ffprobe=binary('ffprobe','FFPROBE_BIN'); ai=binary('realesrgan-ncnn-vulkan','REALESRGAN_BIN')
with st.expander('Engine status', expanded=not bool(ffmpeg)):
    st.write('FFmpeg:',ffmpeg or 'Not found')
    st.write('FFprobe:',ffprobe or 'Not found')
    st.write('Real-ESRGAN:',ai or 'Not found (AI mode unavailable)')
    st.caption('For AI mode, install the Real-ESRGAN NCNN executable and its models. Use the README setup instructions.')

video=st.file_uploader('Upload video',type=['mp4','avi','3gp'])
mode=st.radio('Enhancement mode',['AI super-resolution (Real-ESRGAN)','Standard resize (FFmpeg fallback)'],horizontal=False)
resolution=st.selectbox('Output resolution',['1080p','1440p','2160p (4K)'])
tile=st.select_slider('AI tile size (smaller uses less memory)',options=[64,128,256,0],value=128)
max_seconds=st.number_input('Process first N seconds (0 = entire video)',min_value=0,max_value=36000,value=10,step=10)
height={'1080p':1080,'1440p':1440,'2160p (4K)':2160}[resolution]
if video:
    st.write(f'File size: {video.size/1024/1024:.1f} MB')
    if video.name.lower().endswith('.mp4'): st.video(video)

if st.button('Enhance video',type='primary',disabled=video is None):
    if not ffmpeg or not ffprobe: st.error('Install FFmpeg: brew install ffmpeg'); st.stop()
    if mode.startswith('AI') and not ai: st.error('Real-ESRGAN executable not found. See README. Alternatively select Standard resize.'); st.stop()
    progress=st.progress(0); status=st.empty()
    try:
        with tempfile.TemporaryDirectory(prefix='clarity_') as td:
            root=Path(td); source=root/('input'+Path(video.name).suffix.lower()); source.write_bytes(video.getbuffer())
            probe=json.loads(run([ffprobe,'-v','error','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate','-of','json',source]))
            stream=probe['streams'][0]; width=int(stream['width']); orig_height=int(stream['height'])
            fps=stream.get('avg_frame_rate','30/1'); fps='30' if fps in ['0/0','N/A'] else fps
            target_w=max(2,round(width*height/orig_height/2)*2)
            output=root/'enhanced.mp4'
            trim=['-t',str(max_seconds)] if max_seconds else []
            if mode.startswith('Standard'):
                status.info('Resizing with FFmpeg (no neural network)')
                run([ffmpeg,'-y','-i',source,*trim,'-vf',f'scale={target_w}:{height}:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','19','-c:a','aac','-b:a','160k','-movflags','+faststart',output]); progress.progress(100)
            else:
                status.info('Extracting frames')
                raw=root/'raw'; up=root/'up'; raw.mkdir(); up.mkdir()
                run([ffmpeg,'-y','-i',source,*trim,'-an',str(raw/'frame_%08d.png')]); progress.progress(20)
                status.info('AI enhancing frames — this may take a while')
                cmd=[ai,'-i',raw,'-o',up,'-n','realesrgan-x4plus','-s','4','-f','png','-t',str(tile)]
                # The model files must be located relative to the executable or set using -m.
                models=Path(ai).parent/'models'
                if models.is_dir(): cmd += ['-m',models]
                run(cmd,cwd=Path(ai).parent); progress.progress(75)
                status.info('Encoding enhanced MP4')
                run([ffmpeg,'-y','-framerate',fps,'-i',str(up/'frame_%08d.png'),'-i',source,*trim,'-map','0:v:0','-map','1:a:0?','-vf',f'scale={target_w}:{height}:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','19','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',output]); progress.progress(100)
            st.session_state['output_bytes']=output.read_bytes()
            status.success('Conversion complete')
    except Exception as e:
        st.error('Conversion failed. Expand details below.')
        with st.expander('Technical error details',expanded=True): st.code(str(e))
if 'output_bytes' in st.session_state:
    st.download_button('Download enhanced MP4',st.session_state['output_bytes'],file_name='clarity_enhanced.mp4',mime='video/mp4')
