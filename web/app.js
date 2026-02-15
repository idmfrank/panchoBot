const planBtn = document.getElementById('planBtn');
const planSummary = document.getElementById('planSummary');
const actionsRoot = document.getElementById('actions');

let actions = [];

async function post(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-session-id': 'web-session' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
  return data;
}

async function get(path) {
  const res = await fetch(path);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
  return data;
}

function ttlText(ts) {
  if (!ts) return 'n/a';
  const left = Math.max(0, ts - Math.floor(Date.now() / 1000));
  return `${left}s`;
}

function render() {
  actionsRoot.innerHTML = '';
  actions.forEach((action) => {
    const div = document.createElement('div');
    div.className = 'action';
    div.innerHTML = `
      <div><b>${action.tool_name}</b> - status: ${action.status}</div>
      <div>Action TTL: ${ttlText(action.expires_at)} | Approval TTL: ${ttlText(action.approval_expires_at)}</div>
      <pre>${action.preview}</pre>
      <button data-kind="approve" data-id="${action.action_id}">Approve</button>
      <button data-kind="execute" data-id="${action.action_id}">Execute</button>
      <details><summary>Audit trail</summary><pre>${JSON.stringify(action.audit, null, 2)}</pre></details>
    `;
    actionsRoot.appendChild(div);
  });
}

async function refreshAction(actionId) {
  const updated = await get(`/actions/${actionId}`);
  actions = actions.map((a) => (a.action_id === actionId ? updated : a));
  render();
}

planBtn.onclick = async () => {
  try {
    const goal = document.getElementById('goal').value;
    const data = await post('/agent/plan', { goal });
    planSummary.textContent = data.plan_summary;
    actions = data.actions;
    render();
  } catch (err) {
    alert(err.message);
  }
};

actionsRoot.onclick = async (event) => {
  const target = event.target;
  const kind = target.getAttribute('data-kind');
  const actionId = target.getAttribute('data-id');
  if (!kind || !actionId) return;

  try {
    if (kind === 'approve') {
      await post('/actions/approve', { action_id: actionId });
      await refreshAction(actionId);
    }
    if (kind === 'execute') {
      await post('/actions/execute', { action_id: actionId });
      await refreshAction(actionId);
    }
  } catch (err) {
    alert(err.message);
  }
};

setInterval(async () => {
  for (const action of actions) {
    await refreshAction(action.action_id);
  }
}, 1000);
