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
