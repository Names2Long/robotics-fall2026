"""Progressive operations with independent inputs and explicit prerequisites."""
from perception.dataset import tuning_image, source_mask
from lab.ui import picture

STEPS = ('Pixels and resolution', 'RGB and BGR channels', 'Grayscale', 'HSV channels',
         'Resize', 'Crop', 'Brightness and contrast', 'Gaussian and median smoothing',
         'Threshold masks', 'Erosion', 'Dilation', 'Opening', 'Closing',
         'Compare all four morphology operations', 'Contours, area and shape', 'Centroids and bounding boxes')

EXPLANATIONS = (
    'An image is a grid of pixels. Resolution is its width and height in pixels. Coordinates (x, y) count columns from the left and rows from the top, starting at (0, 0). Click the scene above or use the sliders. OpenCV stores each color pixel as blue, green and red values from 0 to 255.',
    'A channel is one number at every pixel. RGB orders these numbers red, green, blue. OpenCV uses BGR. These are the same measurements in a different order. Each single-channel view below is grayscale: bright means more of that channel, not a gray object. Coordinates are not needed to compare the complete channel images.',
    'Grayscale converts three color numbers into one brightness-like number, using a weighted combination. Different colors can become the same gray. Compare the original scene with the grayscale result. Color cannot be recovered from the grayscale image alone.',
    'HSV separates hue, saturation and value. Hue describes a color family, saturation describes color intensity, and value describes brightness. OpenCV hue runs from 0 to 179. Saturation and value run from 0 to 255. Hue is unreliable for nearly gray pixels. Bright in a channel view means a larger number, not greater certainty.',
    'Resize changes the number of pixels representing the complete scene. It does not select a smaller region. Downsampling can remove small details. The three results show the same field of view at different resolutions, displayed at their native sizes so the difference remains visible.',
    'Crop selects a rectangular part of the original scene without rescaling its pixels. Unlike resizing, this removes surrounding context. Coordinates inside the crop start at a new origin. Select its columns and rows, then compare the marked source with the retained region.',
    'Brightness adds an offset to each channel. Contrast multiplies values. Values beyond 0 to 255 are clipped, which loses detail. Compare one change at a time against the original scene. These examples do not become the inputs to later lessons.',
    'Smoothing uses nearby pixels. Gaussian smoothing takes a weighted average. Median smoothing takes the middle neighborhood value. Each result starts from the same fixed noisy scene. Compare removal of isolated specks and loss of sharp boundaries at kernel widths 3 and 9.',
    'An HSV threshold tests whether all three channel values fall within chosen ranges. White mask pixels pass. Black pixels fail. This rule selects colors, not object identities. The desk can match the mug. Change a bound, run, and inspect what enters or leaves the mask.',
    'Erosion shrinks white regions. A pixel remains white only if the whole square kernel fits inside nearby foreground. Compare widths 1, 3 and 9 on the same fixed input mask. Width 1 does nothing. Larger kernels can erase small regions.',
    'Dilation expands white regions where the square neighborhood touches foreground. It can join gaps but also merge separate objects. All three outputs use exactly the same input mask, not the erosion result from the previous lesson.',
    'Opening is erosion followed by dilation. It removes small specks while restoring surviving larger regions. Compare three kernel widths. A removed target cannot be restored by the dilation. Each result starts from the fixed input mask.',
    'Closing is dilation followed by erosion. It fills narrow holes or gaps. Large kernels can merge objects. Here each result starts from the fixed raw mask, not a mask opened in an earlier lesson, so you can isolate closing itself.',
    'Compare erosion, dilation, opening and closing on exactly the same mask with the same kernel. Erosion shrinks foreground, dilation expands it, opening removes small foreground specks, and closing fills small background gaps. Look for a small target that disappears or separate regions that merge. No operation knows which pixels belong to the mug.',
    'Contours trace connected mask boundaries. Area measures enclosed pixels. Circularity compares area with perimeter and is near 1 for a circle. The detector chooses the largest contour passing the area and circularity rules. Its choice can still be the wrong object. Inspect the numbered candidates and eligibility table.',
    'A bounding box is (x, y, width, height). Its center is the midpoint of that rectangle. A contour centroid is the balance point of the enclosed region. The handle makes these differ. This geometry demonstration uses a supplied hand-traced mug silhouette so the lesson works even when color detection fails. It is not a prediction or evidence that a detector succeeded.'
)

PREFIX = 'import cv2\nimport numpy as np\n# Start from the original desk photograph every time.\n'
FIXED_MASK = ('hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)\n'
              'raw_mask = cv2.inRange(hsv, np.array([0, 70, 25]), np.array([35, 255, 180]))\n')


def move(st, progress, step):
    from lab.autosave import save
    st.session_state['settings']['playground_progress'] = {**progress, 'step': step}
    st.session_state['scroll_to_top'] = True
    save(st)
    st.rerun()


def render(st):
    st.header('Guided image playground')
    st.write('Starting question: how can pixel operations help a robot locate a mug among desk equipment? Work through one topic at a time. Read its explanation, run the displayed code and compare the output with the source scene.')
    image = tuning_image()
    progress = st.session_state['settings'].setdefault('playground_progress', {})
    if progress.get('version') != 4:
        # Only tutorial progress changes. Earlier mission writing is untouched.
        progress = {'version': 4, 'step': 0, 'finished': False}
        st.session_state['settings']['playground_progress'] = progress
    step = min(max(int(progress.get('step', 0)), 0), len(STEPS)-1)
    if step == 0:
        from lab.pixel_picker import picker
        st.session_state.setdefault('lesson.pixel_x', 240)
        st.session_state.setdefault('lesson.pixel_y', 160)
        picker(st, image)
    else:
        picture(st, image, 'Original scene: mug, laptop, keyboard and trackpad')
    st.caption('Ryan Riggins, Laptop and a mug, CC0. The mug top is outside the photograph. A robot would need more views and depth before attempting a grasp.')
    st.progress((step+1)/len(STEPS), text=f'Step {step+1} of {len(STEPS)}: {STEPS[step]}')
    st.subheader(STEPS[step])
    st.write(EXPLANATIONS[step])
    st.caption('Independent input: every lesson reloads this original scene. Mask operations rebuild a fixed prerequisite mask shown with the output. No slider setting or result from another lesson is inherited.')
    controls, program = st.columns([1, 1.4])
    source = PREFIX
    views = []
    if step == 0:
        x = controls.slider('Pixel x', 0, image.shape[1]-1, key='lesson.pixel_x')
        y = controls.slider('Pixel y', 0, image.shape[0]-1, key='lesson.pixel_y')
        source += f'x, y = {x}, {y}\npixel = image[y, x]\noutput = image.copy()\ncv2.drawMarker(output, (x, y), (0, 255, 0), markerSize=16)'
        views = [('output', 'Selected pixel location')]
    elif step == 1:
        source += "rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)\nred = rgb[:, :, 0]\ngreen = rgb[:, :, 1]\nblue = rgb[:, :, 2]"
        views = [('red', 'Red-channel strength'), ('green', 'Green-channel strength'), ('blue', 'Blue-channel strength')]
    elif step == 2:
        source += 'output = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)'
        views = [('image', 'Original color'), ('output', 'Grayscale')]
    elif step == 3:
        source += "hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)\nhue = (hsv[:, :, 0].astype(float) * 255 / 179).astype('uint8')\nsaturation = hsv[:, :, 1]\nvalue = hsv[:, :, 2]"
        views = [('hue', 'Hue, scaled for display'), ('saturation', 'Saturation'), ('value', 'Value / brightness')]
    elif step == 4:
        for width in (120, 240, 480):
            height = round(image.shape[0]*width/image.shape[1])
            source += f'resized_{width} = cv2.resize(image, ({width}, {height}), interpolation=cv2.INTER_AREA)\n'
            views.append((f'resized_{width}', f'{width} by {height} pixels'))
    elif step == 5:
        left, right = controls.slider('Crop columns', 0, 480, (230, 390), key='lesson.crop_x')
        top, bottom = controls.slider('Crop rows', 0, 320, (0, 125), key='lesson.crop_y')
        if left == right or top == bottom:
            controls.info('Choose a crop with positive width and height.')
            return
        source += f'marked = image.copy()\ncv2.rectangle(marked, ({left}, {top}), ({right-1}, {bottom-1}), (0, 220, 0), 2)\ncropped = image[{top}:{bottom}, {left}:{right}].copy()'
        views = [('marked', 'Source with retained rectangle'), ('cropped', 'Crop, no resizing')]
    elif step == 6:
        for name, alpha, beta in (('original', 1, 0), ('brighter', 1, 50), ('contrast', 1.5, 0)):
            source += f"{name} = np.clip(image.astype(float) * {alpha} + {beta}, 0, 255).astype('uint8')\n"
            views.append((name, f'Contrast {alpha}, brightness +{beta}'))
    elif step == 7:
        source += 'noisy = image.copy()\nrng = np.random.default_rng(7)\nnoise = rng.random(image.shape[:2])\nnoisy[noise < 0.02] = 0\nnoisy[noise > 0.98] = 255\n'
        views = [('noisy', 'Fixed noisy input')]
        for method in ('Gaussian', 'median'):
            for kernel in (3, 9):
                name = f'{method}_{kernel}'
                call = f'cv2.GaussianBlur(noisy, ({kernel}, {kernel}), 0)' if method == 'Gaussian' else f'cv2.medianBlur(noisy, {kernel})'
                source += f'{name} = {call}\n'
                views.append((name, f'{method}, kernel {kernel}'))
    elif step == 8:
        bounds = []
        for name, maximum, initial in (('Hue', 179, (0, 35)), ('Saturation', 255, (70, 255)), ('Value', 255, (25, 180))):
            bounds.append(controls.slider(name, 0, maximum, initial, key='lesson.'+name.lower()))
        low, high = [a[0] for a in bounds], [a[1] for a in bounds]
        source += f'hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)\nraw_mask = cv2.inRange(hsv, np.array({low}), np.array({high}))'
        views = [('image', 'Original scene'), ('raw_mask', 'White pixels pass every bound')]
    elif step in (9, 10, 11, 12):
        source += FIXED_MASK
        views = [('raw_mask', 'Fixed input: H 0 to 35, S 70 to 255, V 25 to 180')]
        for kernel in (1, 3, 9):
            name = f'kernel_{kernel}'
            call = f'cv2.erode(raw_mask, kernel)' if step == 9 else 'cv2.dilate(raw_mask, kernel)' if step == 10 else f"cv2.morphologyEx(raw_mask, cv2.MORPH_{'OPEN' if step == 11 else 'CLOSE'}, kernel)"
            source += f'kernel = np.ones(({kernel}, {kernel}), np.uint8)\n{name} = {call}\n'
            views.append((name, f'Kernel {kernel} by {kernel}'))
    elif step == 13:
        size = controls.select_slider('Shared kernel width',(3,5,9),value=5,key='lesson.compare_kernel')
        source += FIXED_MASK + f'kernel = np.ones(({size}, {size}), np.uint8)\n'
        source += 'erosion = cv2.erode(raw_mask, kernel)\ndilation = cv2.dilate(raw_mask, kernel)\nopening = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, kernel)\nclosing = cv2.morphologyEx(raw_mask, cv2.MORPH_CLOSE, kernel)\n'
        views = [('erosion','Erosion: shrink white'),('dilation','Dilation: expand white'),('opening','Opening: remove white specks'),('closing','Closing: fill dark gaps')]
    elif step == 14:
        from perception.classical import Settings
        from perception.lesson import code_for
        area = controls.slider('Minimum contour area (pixels²)', 1, 15000, 300, key='lesson.area')
        shape = controls.slider('Minimum circularity', 0., 1., 0., .05, key='lesson.shape')
        source = code_for(Settings(h_high=35, s_low=70, s_high=255, v_low=25, v_high=180, min_area=area, min_circularity=shape), 'contours')
        views = [('clean', 'Fixed mask after kernel 3 opening and closing'), ('contour_image', 'Numbered contour candidates')]
    else:
        source += '''# teaching_mask is the supplied manual silhouette, not a detector output.
contours, _ = cv2.findContours(teaching_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contour = max(contours, key=cv2.contourArea)
x, y, width, height = cv2.boundingRect(contour)
box_center = (x + width/2, y + height/2)
moments = cv2.moments(teaching_mask, binaryImage=True)
centroid = (moments['m10']/moments['m00'], moments['m01']/moments['m00'])
output = image.copy()
cv2.drawContours(output, [contour], -1, (255, 180, 0), 2)
cv2.rectangle(output, (x,y), (x+width,y+height), (0,220,0), 2)
cv2.circle(output, tuple(map(int, box_center)), 6, (0,0,255), 2)
cv2.drawMarker(output, tuple(map(int, centroid)), (0,255,255), markerSize=12)
cv2.line(output, (240,0), (240,319), (255,0,255), 1)
detail = output[max(0,y-5):min(320,y+height+10), max(0,x-5):min(480,x+width+10)].copy()
'''
        views = [('output', 'Green box, red box center, yellow centroid, magenta image center'), ('detail', 'Enlarged region for comparing the two centers')]
    program.caption('Run executes the displayed code on a fresh copy of the original image.')
    with program.container(height=280):
        st.code(source, language='python', wrap_lines=True)
    run_key = (step, source)
    if program.button('Run this step', type='primary', key='lesson.run'):
        output = {'image': image.copy(), 'teaching_mask': source_mask().astype('uint8')*255}
        exec(compile(source, '<guided playground>', 'exec'), output)
        st.session_state['lesson_output'] = {'key': run_key, 'values': {k:v for k,v in output.items() if k not in ('cv2', 'np', '__builtins__', 'rng')}}
    recorded = st.session_state.get('lesson_output', {})
    current = recorded.get('key') == run_key
    if current:
        output = recorded['values']
        st.subheader('Output from your run')
        if step == 4:
            for name, caption in views:
                st.image(output[name], channels='BGR', width=output[name].shape[1], caption=caption)
        else:
            # At most three small panels per row, never a screen-height figure.
            if step == 13: st.image(output['raw_mask'],caption='Common input mask for all four operations',width=240)
            panel_count = 2 if step == 13 else 3
            for start in range(0, len(views), panel_count):
                group = views[start:start+panel_count]
                for column, (name, caption) in zip(st.columns(len(group)), group):
                    picture(column, output[name], caption)
        if step == 0:
            a, b = st.columns([2, 1])
            pixel = output['pixel'].tolist()
            a.write(f'Resolution: 480 by 320 pixels. Pixel ({x}, {y}) has BGR {pixel}.')
            import numpy as np
            swatch = np.full((60,60,3), pixel, dtype='uint8')
            b.image(swatch, channels='BGR', width=60, caption='Selected color')
        if step == 14:
            st.dataframe(output['rows'], hide_index=True)
            st.caption('eligible=True means that candidate passes both filters. The mission will select the largest eligible area, not the region with a known identity.')
        if step == 15:
            st.table([{'Quantity': 'Box (x, y, width, height)', 'Value': str((output['x'],output['y'],output['width'],output['height']))},
                      {'Quantity': 'Box center (x, y)', 'Value': str(output['box_center'])},
                      {'Quantity': 'Contour region centroid (x, y)', 'Value': str(tuple(round(v,1) for v in output['centroid']))},
                      {'Quantity': 'Image center (x, y)', 'Value': '(240, 160)'}])
            st.info('Compare the red ring and yellow cross in the enlarged view. The rectangle balances empty space too, while the silhouette centroid balances only marked pixels. Neither is a physical grasp position. This lesson uses an annotation to teach geometry, not to claim detection success.')
    else:
        st.info('Run this step to see the current output.')
    st.divider()
    left, right = st.columns(2)
    if step and left.button('Back to '+STEPS[step-1], key='lesson.back'):
        move(st, progress, step-1)
    label = 'Continue to '+STEPS[step+1] if step < len(STEPS)-1 else 'Finish playground'
    if right.button(label, disabled=not current, key='lesson.next'):
        if step == len(STEPS)-1:
            progress['finished'] = True
            from lab.autosave import save
            save(st)
            st.rerun()
        move(st, progress, step+1)
    if progress.get('finished'):
        st.success('Playground complete. Continue to the detector investigation.')
    if step == len(STEPS)-1:
        from perception.dataset import ROOT
        reference = ROOT/'scripts/playground_reference.py'
        st.subheader('Keep the documented Python reference')
        st.write('scripts/playground_reference.py contains the operations from every playground step, with explanations and a runnable example. Use it as a reference for the other missions. It is not an additional assignment and does not replace the live ROS camera node.')
        st.code('python scripts/playground_reference.py --output runtime/playground_reference',language='bash')
        st.download_button('Download playground_reference.py',reference.read_bytes(),'playground_reference.py','text/x-python')
