// Contract tests for the actual shipped component script, without a browser dependency.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

test('render handshake and scaled image clicks send original pixel coordinates', () => {
  const html = fs.readFileSync(path.join(__dirname, '../lab/pixel_component/index.html'), 'utf8');
  const source = html.match(/<script>([\s\S]*?)<\/script>/)[1];
  const messages = [];
  let receive;
  const image = { src: '', getBoundingClientRect: () => ({left:10, top:20, width:240, height:160}) };
  const selection = {};
  const sandbox = {
    parent: {postMessage: message => messages.push(message)},
    document: {body:{scrollHeight:200}, getElementById: id => id === 'scene' ? image : selection},
    window: {addEventListener: (name, callback) => {receive = callback;}},
    ResizeObserver: class {observe() {}}, Date, Math
  };
  vm.runInNewContext(source, sandbox);
  assert.equal(messages[0].type, 'streamlit:componentReady');
  receive({data:{type:'streamlit:render', args:{width:480,height:320,image:'encoded-image'}}});
  assert.equal(image.src, 'data:image/png;base64,encoded-image');
  image.onclick({clientX:130,clientY:60});
  const result = messages.at(-1);
  assert.equal(result.type, 'streamlit:setComponentValue');
  assert.equal(result.value.x, 240);
  assert.equal(result.value.y, 80);
  assert.match(selection.textContent, /Selected pixel \(240, 80\)/);
  image.onclick({clientX:250,clientY:180});
  assert.equal(messages.at(-1).value.x,479);
  assert.equal(messages.at(-1).value.y,319);
});
