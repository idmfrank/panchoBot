let current;
const out = document.getElementById('out');

function log(x){ out.textContent = JSON.stringify(x, null, 2); }

async function api(path, data){
  const r = await fetch(path, {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(data)});
  const j = await r.json();
  if(!r.ok) throw new Error(JSON.stringify(j));
  return j;
}

document.getElementById('propose').onclick = async () => {
  current = await api('/actions/propose', { content: document.getElementById('content').value, pubkey: document.getElementById('pubkey').value, tags: [] });
  log(current);
};

document.getElementById('approve').onclick = async () => {
  if (!window.nostr) throw new Error('NIP-07 extension required');
  const payload = current.action_payload;
  const noteBase = { kind: 1, content: payload.content, tags: payload.tags, created_at: payload.created_at, pubkey: payload.pubkey };
  const noteEvent = await window.nostr.signEvent(noteBase);
  const approvalBase = {
    kind: 27235,
    created_at: Math.floor(Date.now()/1000),
    tags: [],
    pubkey: payload.pubkey,
    content: JSON.stringify({action_id: current.action_id, action_hash: current.action_hash})
  };
  const approvalEvent = await window.nostr.signEvent(approvalBase);
  const res = await api('/actions/approve', { action_id: current.action_id, approval_event: approvalEvent, note_event: noteEvent });
  log(res);
};

document.getElementById('execute').onclick = async () => {
  const res = await api('/actions/execute', { action_id: current.action_id });
  log(res);
};
