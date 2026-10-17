// Tiny stand-in for the Design canvas runtime: renders <template id="tpl"> with
// {{dotted.path}} holes, <sc-for list as>, <sc-if value> and onClick handlers.
// ponytail: re-renders the whole screen on every setState; fine for 14 mock screens.
class DCLogic {
  constructor(props) { this.props = props || {}; this.state = {}; }
  setState(patch) { Object.assign(this.state, patch); this._render(); }
}

function mount(Component) {
  const tpl = document.getElementById('tpl');
  const root = document.getElementById('dc');
  const comp = new Component({});
  // Build in an inert document so <img src="{{hole}}"> never fetches before it is filled.
  const inert = document.implementation.createHTMLDocument('');
  const get = (path, scope) => path.split('.').reduce((o, k) => (o == null ? o : o[k]), scope);
  const fill = (str, scope) => str.replace(/\{\{\s*([\w.$]+)\s*\}\}/g, (_, p) => { const v = get(p, scope); return v == null ? '' : v; });

  function walk(node, scope) {
    for (const child of [...node.childNodes]) {
      if (child.nodeType === 3) { if (child.data.includes('{{')) child.data = fill(child.data, scope); continue; }
      if (child.nodeType !== 1) continue;
      const tag = child.tagName.toLowerCase();
      if (tag === 'sc-for') {
        const list = get(child.getAttribute('list').slice(2, -2).trim(), scope) || [];
        const as = child.getAttribute('as');
        const frag = inert.createDocumentFragment();
        for (const item of list) {
          const holder = inert.createElement('div');
          for (const c of child.childNodes) holder.appendChild(c.cloneNode(true));
          walk(holder, { ...scope, [as]: item });
          frag.append(...holder.childNodes);
        }
        child.replaceWith(frag);
        continue;
      }
      if (tag === 'sc-if') {
        if (!get(child.getAttribute('value').slice(2, -2).trim(), scope)) { child.remove(); continue; }
        walk(child, scope);
        child.replaceWith(...child.childNodes);
        continue;
      }
      for (const a of [...child.attributes]) {
        if (a.name.startsWith('hint-')) { child.removeAttribute(a.name); continue; }
        if (!a.value.includes('{{')) continue;
        if (a.name.startsWith('on')) {
          const fn = get(a.value.slice(2, -2).trim(), scope);
          child.removeAttribute(a.name);
          if (typeof fn === 'function') child.addEventListener(a.name.slice(2).toLowerCase(), fn);
          continue;
        }
        child.setAttribute(a.name, fill(a.value, scope));
      }
      walk(child, scope);
    }
  }

  comp._render = () => {
    const holder = inert.createElement('div');
    holder.appendChild(inert.importNode(tpl.content, true));
    walk(holder, comp.renderVals());
    root.replaceChildren(...holder.childNodes);
  };
  comp._render();
}

// Opened on its own (not inside the board): centre the screen and offer a way back.
if (window.top === window.self) {
  const back = () => { location.href = '../index.html'; };
  const css = document.createElement('style');
  css.textContent = `
    body{background:#E9E4DB}
    #dc{display:flex;justify-content:center;padding:24px 16px 48px}
    #dc>div[style*="width: 390px"]{border-radius:44px;box-shadow:0 18px 60px rgba(28,27,25,.16);flex:0 0 auto}
    #dc>div:not([style*="width: 390px"]){flex:1 1 100%;border-radius:14px;overflow:hidden}
    .dc-close{position:fixed;z-index:10;top:calc(16px + env(safe-area-inset-top,0px));right:16px;display:flex;align-items:center;gap:8px;height:44px;padding:0 16px 0 12px;border:1px solid #DDD6CB;border-radius:22px;background:rgba(251,249,245,.94);box-shadow:0 6px 24px rgba(28,27,25,.12);font:500 14px 'Jost',system-ui,sans-serif;color:#1C1B19;cursor:pointer}
    .dc-close kbd{padding:1px 6px;border:1px solid #CFC7BA;border-radius:6px;font:12px 'Jost',system-ui,sans-serif;color:#625B52}
    @media (max-width:520px){#dc{padding:0}#dc>div[style*="width: 390px"]{border-radius:0;box-shadow:none}.dc-close kbd{display:none}}`;
  document.head.appendChild(css);
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'dc-close';
  btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"></path></svg>All screens <kbd>Esc</kbd>';
  btn.addEventListener('click', back);
  document.body.appendChild(btn);
  addEventListener('keydown', (e) => { if (e.key === 'Escape') back(); });
}
