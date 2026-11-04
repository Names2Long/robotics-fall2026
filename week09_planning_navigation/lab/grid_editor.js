export default function(component) {
  const {parentElement, data, setStateValue} = component;
  const canvas = parentElement.querySelector('canvas');
  const context = canvas.getContext('2d');
  const state = JSON.parse(JSON.stringify(data.state));
  const size = 36, rows = state.grid.length, cols = state.grid[0].length;
  canvas.width = cols * size;
  canvas.height = rows * size;
  canvas.style.maxWidth = '100%';
  canvas.style.touchAction = 'none';
  let painting = false;
  parentElement.querySelector('select').value = state.mode || 'wall';
  function draw() {
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      context.fillStyle = state.grid[r][c] ? '#344054' : '#f8fafc';
      context.fillRect(c*size,(rows-1-r)*size,size,size);
      context.strokeStyle = '#98a2b3';
      context.strokeRect(c*size,(rows-1-r)*size,size,size);
    }
    [['start','S','#16804a'],['goal','G','#c12a43']].forEach(([key,label,color]) => {
      const [r,c] = state[key];
      context.fillStyle = color;
      context.fillRect(c*size+3,(rows-1-r)*size+3,size-6,size-6);
      context.fillStyle = 'white'; context.font = 'bold 18px sans-serif';
      context.textAlign = 'center'; context.textBaseline = 'middle';
      context.fillText(label,(c+.5)*size,(rows-r-.5)*size);
    });
  }
  function edit(event) {
    const rect = canvas.getBoundingClientRect();
    const c = Math.floor((event.clientX-rect.left)*cols/rect.width);
    const r = rows-1-Math.floor((event.clientY-rect.top)*rows/rect.height);
    if (r<0 || c<0 || r>=rows || c>=cols) return;
    const mode = parentElement.querySelector('select').value;
    state.mode = mode;
    if (mode === 'start' || mode === 'goal') {
      state[mode] = [r,c]; state.grid[r][c] = 0;
    } else if (![state.start,state.goal].some(p=>p[0]===r && p[1]===c)) {
      state.grid[r][c] = mode === 'wall' ? 1 : 0;
    }
    draw();
  }
  canvas.onpointerdown = event => {
    painting = true; canvas.setPointerCapture(event.pointerId); edit(event);
  };
  canvas.onpointermove = event => { if (painting) edit(event); };
  canvas.onpointerup = () => { painting = false; setStateValue('state',state); };
  canvas.onpointercancel = () => { painting = false; setStateValue('state',state); };
  draw();
}
