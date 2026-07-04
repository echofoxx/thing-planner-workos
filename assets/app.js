const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const STORAGE_KEY = 'thing-planner-workos-v090-state';
const API_BASE = window.THING_PLANNER_API_BASE || '/api';
let apiOnline = false;
let apiStatusText = 'Local demo mode';
let hasBootstrappedApi = false;
let suppressApiSync = false;
let syncTimer = null;
let lastSyncAt = null;
let authToken = localStorage.getItem('thing-planner-workos-v090-token') || null;
let currentUser = null;
let authStatusText = 'Demo auth pending';
let lastReportDataset = null;
let reportStatusText = 'Local intake automation engine';
let lastGanttDataset = null;
let ganttStatusText = 'Local Gantt dependency engine';

const seedState = {
  module: 'home',
  view: 'list',
  selectedProject: 'p1',
  selectedDoc: 'doc1',
  knowledgeQuery: '',
  helper: true,
  aiPromo: true,
  version: '0.9.0',
  workspace: {
    name: "Adrian Francis's Workspace",
    initials: 'A',
  },
  members: [
    { id: 'adrian', name: 'Adrian Francis', initials: 'AF', avatar: 'purple', role: 'Workspace Owner' },
    { id: 'mira', name: 'Mira Chen', initials: 'MC', avatar: 'blue', role: 'Project Lead' },
    { id: 'tom', name: 'Tom Reyes', initials: 'TR', avatar: 'orange', role: 'Engineer' },
    { id: 'nina', name: 'Nina Patel', initials: 'NP', avatar: 'green', role: 'Designer' },
  ],
  spaces: [
    {
      id: 's1',
      name: 'Team Space',
      icon: '👥',
      folders: [
        {
          id: 'f1',
          name: 'Projects',
          icon: '📁',
          lists: [
            { id: 'p1', name: 'Project 1', icon: '☑', kind: 'project' },
            { id: 'p2', name: 'Project 2', icon: '☑', kind: 'project' },
            { id: 'doc1', name: 'Project Notes', icon: '📄', kind: 'doc' },
          ],
        },
      ],
    },
  ],
  tasks: [
    { id: 't1', projectId: 'p1', name: 'Task 1', assignee: 'mira', due: '2026-07-07', priority: 'High', status: 'TO DO', comments: [{ by: 'Adrian Francis', text: 'Need kickoff checklist before assigning to the team.' }], estimate: 3, tracked: 0.5, billable: true, tags: ['Kickoff'], progress: 0, description: 'Initial planning task for the launch project.', start: '2026-07-04', duration: 3, critical: false },
    { id: 't2', projectId: 'p1', name: 'Task 2', assignee: 'tom', due: '2026-07-08', priority: 'Normal', status: 'TO DO', comments: [], estimate: 5, tracked: 1.5, billable: true, tags: ['Engineering'], progress: 0, description: 'Build the core task workflow and validate drag/drop.', start: '2026-07-05', duration: 4, critical: true },
    { id: 't3', projectId: 'p1', name: 'Task 3', assignee: 'nina', due: '2026-07-10', priority: 'Low', status: 'TO DO', comments: [], estimate: 2, tracked: 0, billable: false, tags: ['Design'], progress: 0, description: 'Polish empty states and template cards.', start: '2026-07-06', duration: 2, critical: false },
    { id: 't4', projectId: 'p1', name: 'Campaign dashboard wireframe', assignee: 'adrian', due: '2026-07-05', priority: 'Urgent', status: 'IN PROGRESS', comments: [{ by: 'Mira Chen', text: 'Use KPI cards that drill into source work.' }], estimate: 4, tracked: 2.25, billable: true, tags: ['Dashboard'], progress: 45, description: 'Create actionable reporting cards for team productivity, campaigns, and billable hours.', start: '2026-07-04', duration: 4, critical: true },
    { id: 't5', projectId: 'p1', name: 'Project intake form automation', assignee: 'mira', due: '2026-07-06', priority: 'High', status: 'BLOCKED', comments: [{ by: 'Tom Reyes', text: 'Blocked until custom field mapping is ready.' }], estimate: 6, tracked: 2, billable: true, tags: ['Forms'], progress: 25, description: 'Route form submissions into the right project with owner, priority, and AI summary.', start: '2026-07-05', duration: 5, critical: true },
    { id: 't6', projectId: 'p1', name: 'AI planner daily schedule', assignee: 'adrian', due: '2026-07-09', priority: 'Normal', status: 'DONE', comments: [], estimate: 3, tracked: 3, billable: false, tags: ['AI'], progress: 100, description: 'Generate a priority-based schedule using tasks, calendar events, and goals.', start: '2026-07-03', duration: 3, critical: false },
    { id: 't7', projectId: 'p2', name: 'Client CRM pipeline template', assignee: 'nina', due: '2026-07-13', priority: 'High', status: 'IN PROGRESS', comments: [], estimate: 7, tracked: 1, billable: true, tags: ['CRM'], progress: 20, description: 'Create agency/client pipeline template.', start: '2026-07-08', duration: 5, critical: false },
    { id: 't8', projectId: 'p2', name: 'GitHub automation proof of concept', assignee: 'tom', due: '2026-07-11', priority: 'Normal', status: 'TO DO', comments: [], estimate: 6, tracked: 0, billable: false, tags: ['Engineering'], progress: 0, description: 'Attach commits and PRs to tasks.', start: '2026-07-08', duration: 3, critical: false },
  ],
  notifications: [
    { id: 'n1', type: 'mention', title: 'Mira mentioned you in Campaign dashboard wireframe', source: 'Task', read: false, tab: 'Primary' },
    { id: 'n2', type: 'risk', title: 'Project intake form automation is blocked', source: 'Risk', read: false, tab: 'Primary' },
    { id: 'n3', type: 'ai', title: 'AI found 2 schedule risks in Project 1', source: 'AI', read: false, tab: 'Other' },
  ],
  dashboards: [
    { id: 'd1', name: 'Executive PMO Dashboard', private: false, favorite: true },
  ],
  reportCards: [
    { id: 'rc1', title: 'Open Tasks', type: 'kpi', metric: 'open_tasks' },
    { id: 'rc2', title: 'Blocked Work', type: 'kpi', metric: 'blocked_tasks' },
    { id: 'rc3', title: 'Billable Hours', type: 'kpi', metric: 'billable_hours' },
    { id: 'rc4', title: 'Project Health', type: 'ai', metric: 'health' },
    { id: 'rc5', title: 'Work by Status', type: 'chart', metric: 'by_status' },
    { id: 'rc6', title: 'Team Productivity', type: 'chart', metric: 'by_assignee' },
    { id: 'rc7', title: 'Actionable Work Table', type: 'table', metric: 'work_table' },
  ],
  reportFilter: 'all',
  forms: [
    { id: 'form1', name: 'Project Intake', description: 'Streamline new project requests', submissions: 3, favorite: false, schema: { mode:'task_intake', target_project_id:'p1', ai_analysis:true } },
    { id: 'form2', name: 'IT Requests', description: 'Triage and prioritize service requests', submissions: 7, favorite: true, schema: { mode:'service_request', target_project_id:'p2', ai_analysis:true } },
  ],
  formSubmissions: [
    { id:'sub-demo-1', formId:'form1', requester:'Adrian Francis', department:'Product', priority:'High', payload:{project_name:'Customer launch dashboard'}, aiAnalysis:{classification:'Project Intake', risk:'medium', recommended_owner:'mira', duplicate_risk:'medium'}, createdTaskId:'t1', status:'Processed', createdAt:'2026-07-04T09:00:00Z' },
    { id:'sub-demo-2', formId:'form1', requester:'Mira Chen', department:'Operations', priority:'Normal', payload:{project_name:'Weekly report automation'}, aiAnalysis:{classification:'Project Intake', risk:'low', recommended_owner:'mira', duplicate_risk:'low'}, createdTaskId:'t5', status:'Processed', createdAt:'2026-07-04T10:00:00Z' },
  ],
  docs: [
    { id: 'doc1', title: 'Project Charter', kind: 'Project Plan', owner: 'Adrian Francis', updated: 'Today', linkedTasks: 4, decisionCount: 1, content: '# Project Charter\n\n## BLUF\nThing Planner WorkOS is an AI-native command center connecting tasks, dashboards, forms, planner blocks, Gantt dependencies, and knowledge.\n\n## Outcomes\n- Deliver a production-demo workspace shell.\n- Keep project artifacts linked back to tasks.\n- Use AI summaries for executive updates and blockers.' },
    { id: 'doc2', title: 'Team SOP Wiki', kind: 'Wiki', owner: 'Mira Chen', updated: 'Yesterday', linkedTasks: 2, decisionCount: 0, content: '# Team SOP Wiki\n\n## Standard workflow\n1. Capture requests through Forms.\n2. Convert approved requests into tasks and linked docs.\n3. Track delivery through List, Board, Calendar, Gantt, and Dashboard views.\n4. Review AI risk watch and update blocked tasks daily.' },
    { id: 'doc3', title: 'Decision Log', kind: 'Decisions', owner: 'Adrian Francis', updated: '2 days ago', linkedTasks: 6, decisionCount: 3, content: '# Decision Log\n\n## Decisions\n- Use PostgreSQL as the production data layer with SQLite fallback for demos.\n- Keep the UI ClickUp-inspired while using independent product identity and assets.\n- Prioritize actionable dashboards before advanced chat features.' },
  ],
  knowledgeStats: { docs: 3, pages: 3, linkedTasks: 12, decisions: 4, verifiedPages: 2 },
  goals: [
    { id: 'g1', name: 'Launch production-ready PM demo', owner: 'Adrian Francis', progress: 42, status: 'At Risk' },
    { id: 'g2', name: 'Reduce project handoff cycle time', owner: 'Mira Chen', progress: 68, status: 'On Track' },
    { id: 'g3', name: 'Reach 90% billable time accuracy', owner: 'Tom Reyes', progress: 74, status: 'On Track' },
  ],
  automations: [
    { id: 'a1', name: 'Escalate blocked tasks', category: 'Automate Projects', enabled: true, trigger: 'Status changes to BLOCKED', action: 'Notify owner and create risk card' },
    { id: 'a2', name: 'Schedule dependent work', category: 'Automate Scheduling', enabled: true, trigger: 'Due date changes', action: 'Shift dependent tasks and flag conflicts' },
    { id: 'a3', name: 'PR updates task status', category: 'Automate Engineering', enabled: false, trigger: 'GitHub PR opened', action: 'Move task to In Review' },
    { id: 'a4', name: 'Lead form to CRM task', category: 'Automate Agencies', enabled: true, trigger: 'New lead form submitted', action: 'Create deal and follow-up task' },
    { id: 'auto_intake_classify', name: 'AI classify new intake', category: 'AI & Automation', enabled: true, trigger: 'Form submitted', action: 'Analyze request and recommend owner/priority' },
    { id: 'auto_intake_task', name: 'Create kickoff task from form', category: 'Automate Projects', enabled: true, trigger: 'Form submitted', action: 'Create mapped task with owner and tags' },
    { id: 'auto_intake_notify', name: 'Notify project owner on intake', category: 'Automate Scheduling', enabled: true, trigger: 'Intake task created', action: 'Notify owner and add intake comment' },
  ],
  automationRuns: [
    { id:'run-demo-1', automationId:'auto_intake_classify', trigger:'Form submitted', sourceType:'form_submission', sourceId:'sub-demo-1', status:'success', summary:'AI classified new intake and recommended owner', details:{form_id:'form1', task_id:'t1'}, createdAt:'2026-07-04T09:01:00Z' },
    { id:'run-demo-2', automationId:'auto_intake_task', trigger:'Form submitted', sourceType:'form_submission', sourceId:'sub-demo-1', status:'success', summary:'Created kickoff task from mapped form fields', details:{form_id:'form1', task_id:'t1'}, createdAt:'2026-07-04T09:02:00Z' },
  ],
  taskDependencies: [
    { id:'dep_t1_t4', predecessorId:'t1', successorId:'t4', type:'FS', lagDays:0, critical:false },
    { id:'dep_t2_t5', predecessorId:'t2', successorId:'t5', type:'FS', lagDays:1, critical:true },
    { id:'dep_t4_t5', predecessorId:'t4', successorId:'t5', type:'FS', lagDays:0, critical:true },
    { id:'dep_t5_t3', predecessorId:'t5', successorId:'t3', type:'FS', lagDays:0, critical:true },
    { id:'dep_t7_t8', predecessorId:'t7', successorId:'t8', type:'FS', lagDays:0, critical:false },
  ],
  ganttBaselines: [],
  ganttRiskAlerts: [],
  ganttMetrics: {},
  aiMessages: [],
};

let state = loadState();
ensurePlannerState();
ensureGanttState();
ensureWhiteboardState();
let activeHomeTab = 'Primary';
let formBuilderOpen = false;
let selectedTaskId = null;

function loadState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return { ...seedState, ...JSON.parse(saved) };
  } catch (e) { console.warn('Could not load saved state', e); }
  return structuredClone(seedState);
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  if (apiOnline && hasBootstrappedApi && !suppressApiSync) scheduleApiSync();
}

function scheduleApiSync() {
  clearTimeout(syncTimer);
  syncTimer = setTimeout(syncStateToApi, 450);
}

async function syncStateToApi() {
  if (!apiOnline) return;
  try {
    await fetch(`${API_BASE}/state`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ state })
    });
    lastSyncAt = new Date();
    apiStatusText = 'API synced';
  } catch (error) {
    apiOnline = false;
    apiStatusText = 'API offline - local mode';
    console.warn('API sync failed', error);
  }
}

function authHeaders() {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {};
}

async function ensureDemoAuth() {
  if (!apiOnline) return;
  try {
    let response;
    if (authToken) {
      response = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders(), cache: 'no-store' });
      if (response.ok) {
        const me = await response.json();
        currentUser = me.user;
        authStatusText = `Signed in: ${currentUser.display_name || currentUser.email}`;
        return;
      }
    }
    response = await fetch(`${API_BASE}/auth/demo-login`, { method: 'POST' });
    if (response.ok) {
      const data = await response.json();
      authToken = data.token;
      currentUser = data.user;
      localStorage.setItem('thing-planner-workos-v090-token', authToken);
      authStatusText = `Demo auth: ${currentUser.display_name || currentUser.email}`;
    }
  } catch (error) {
    authStatusText = 'Auth offline';
    console.warn('Demo auth failed', error);
  }
}

async function hydrateFromApi() {
  try {
    const health = await fetch(`${API_BASE}/health`, { cache: 'no-store' });
    if (!health.ok) throw new Error('Health check failed');
    const healthJson = await health.json();
    const response = await fetch(`${API_BASE}/state`, { cache: 'no-store' });
    if (!response.ok) throw new Error('State fetch failed');
    const data = await response.json();
    apiOnline = true;
    apiStatusText = `${healthJson.version || 'v0.9.0'} ${healthJson.schema || 'API'} connected`;
    await ensureDemoAuth();
    hasBootstrappedApi = true;
    if (data && data.state) {
      suppressApiSync = true;
      state = { ...state, ...data.state };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      render();
      await refreshReportDataset(true);
      suppressApiSync = false;
    }
  } catch (error) {
    apiOnline = false;
    apiStatusText = 'API offline - local mode';
    hasBootstrappedApi = true;
    console.warn('Using local demo data because API is unavailable', error);
    const badge = document.querySelector('.api-status-badge');
    if (badge) { badge.textContent = apiStatusText; badge.classList.remove('online'); badge.classList.add('offline'); }
  }
}

async function refreshReportDataset(silent=false) {
  if (!apiOnline) {
    lastReportDataset = computeLocalReportDataset();
    reportStatusText = 'Local intake automation engine';
    if (!silent) toast('Reports refreshed locally');
    return lastReportDataset;
  }
  try {
    const response = await fetch(`${API_BASE}/reports/dashboard?dashboard_id=d1`, { headers: authHeaders(), cache: 'no-store' });
    if (!response.ok) throw new Error('Report API failed');
    lastReportDataset = await response.json();
    reportStatusText = 'Server intake automation engine synced';
    if (!silent) toast('Dashboard report data refreshed from API');
    return lastReportDataset;
  } catch (error) {
    lastReportDataset = computeLocalReportDataset();
    reportStatusText = 'Report API offline - local derived data';
    if (!silent) toast('Report/Form API offline; using local analytics');
    return lastReportDataset;
  }
}

async function resetDemoData() {
  localStorage.removeItem(STORAGE_KEY);
  state = structuredClone(seedState);
  if (apiOnline) {
    try { await fetch(`${API_BASE}/reset`, { method: 'POST' }); } catch (error) { console.warn('API reset failed', error); }
  }
  toast('Demo data reset');
  render();
}

function toast(message) {
  let el = $('.toast');
  if (!el) {
    el = document.createElement('div');
    el.className = 'toast';
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2200);
}

const railItems = [
  ['home', '⌂', 'Home'],
  ['spaces', '🪐', 'Spaces'],
  ['planner', '▣', 'Planner'],
  ['ai', '✽', 'AI'],
  ['teams', '♙', 'Teams'],
  ['docs', '▤', 'Docs'],
  ['dashboards', '▥', 'Dashboa...'],
  ['whiteboards', '✎', 'Whitebo...'],
  ['forms', '☑', 'Forms'],
  ['clips', '▰', 'Clips'],
  ['goals', '♕', 'Goals'],
  ['more', '⋮', 'More'],
];

const bottomRailItems = [
  ['invite', '♙+', 'Invite'],
  ['upgrade', '⬆', 'Upgrade'],
];

function render() {
  saveState();
  const app = $('#app');
  app.innerHTML = `
    ${renderTopbar()}
    <div class="main">
      ${renderRail()}
      ${renderSidebar()}
      <main class="canvas">
        ${renderPromoBanner()}
        ${renderMain()}
      </main>
    </div>
    ${renderTaskDrawer()}
    <div class="drawer-backdrop ${selectedTaskId ? 'show' : ''}" onclick="closeTaskDrawer()"></div>
    <div class="toast"></div>
  `;
  bindEvents();
}

function renderTopbar() {
  return `
  <header class="topbar">
    <div class="top-left-mini">
      <button class="workspace-picker" onclick="toast('Workspace switcher opened')">
        <span class="workspace-avatar">${state.workspace.initials}</span>
        <span>${escapeHtml(state.workspace.name)}</span>
        <span>⌄</span>
      </button>
      <button class="top-icon" onclick="setModule('planner')">▣</button>
      <button class="top-icon" onclick="toast('No workspace warnings today')">⚠</button>
      <span class="api-status-badge ${apiOnline ? 'online' : 'offline'}" title="v0.9 Whiteboards/canvas/mind maps/data/auth status">${apiStatusText}</span><span class="api-status-badge ${currentUser ? 'online' : 'offline'}" title="Demo authentication">${currentUser ? (currentUser.initials || 'AF') + ' Auth' : authStatusText}</span>
    </div>
    <div class="global-search-wrap">
      <label class="global-search"><span>⌕</span><input id="globalSearch" placeholder="Search ⌘K" onkeydown="if(event.key==='Enter') globalSearch(this.value)" /></label>
      <button class="ai-pill" onclick="setModule('ai')"><span class="ai-flower">✽</span> AI Chats</button>
    </div>
    <div class="top-actions">
      <button class="top-icon" title="Sync">⟳</button>
      <button class="top-icon" title="Portfolio">▤</button>
      <button class="top-icon" title="Tasks">☷</button>
      <button class="top-icon" title="Files">▱</button>
      <button class="top-icon" title="Mic">♩</button>
      <button class="top-icon" title="Timer">◷</button>
      <button class="top-icon" title="Docs">▤</button>
      <button class="top-icon" title="Settings" onclick="toast('Workspace settings placeholder')">⚙</button>
      <button class="profile" onclick="toast('Profile menu placeholder')"><span class="avatar small">AF</span><span>⌄</span></button>
    </div>
  </header>`;
}

function renderRail() {
  return `<aside class="rail">
    ${railItems.map(([id, ico, label]) => `
      <button class="rail-item ${state.module === id ? 'active' : ''}" onclick="setModule('${id}')"><span class="ico">${ico}</span><span>${label}</span></button>`).join('')}
    <div class="rail-spacer"></div>
    ${bottomRailItems.map(([id, ico, label]) => `
      <button class="rail-item ${state.module === id ? 'active' : ''}" onclick="setModule('${id}')"><span class="ico">${ico}</span><span>${label}</span></button>`).join('')}
  </aside>`;
}

function renderPromoBanner() {
  if (state.module === 'spaces') return `
    <div class="promo-banner">Point AI at a messy project. Get a rescue plan in seconds. <a href="#" onclick="setModule('ai')">Reveal the plan →</a><button class="promo-close" onclick="dismissBanner()">×</button></div>
  `;
  if (['home','forms','dashboards','ai'].includes(state.module)) return `
    <div class="promo-banner">Point AI at a messy project. Get a rescue plan in seconds. <a href="#" onclick="setModule('ai')">Reveal the plan →</a><button class="promo-close" onclick="dismissBanner()">×</button></div>
  `;
  return '';
}

function dismissBanner() {
  const b = $('.promo-banner');
  if (b) b.remove();
}

function setModule(module) {
  state.module = module;
  if (module === 'spaces') state.view = state.view || 'list';
  render();
}

function renderSidebar() {
  switch (state.module) {
    case 'home': return renderHomeSidebar();
    case 'spaces': return renderSpacesSidebar();
    case 'forms': return renderFormsSidebar();
    case 'dashboards': return renderDashboardSidebar();
    case 'ai': return renderAISidebar();
    case 'planner': return renderPlannerSidebar();
    case 'teams': return renderTeamsSidebar();
    case 'docs': return renderDocsSidebar();
    case 'whiteboards': return renderWhiteboardSidebar();
    case 'goals': return renderGoalsSidebar();
    case 'clips': return renderClipsSidebar();
    case 'more': return renderMoreSidebar();
    case 'automations': return renderMoreSidebar();
    case 'invite': return renderInviteSidebar();
    case 'upgrade': return renderUpgradeSidebar();
    default: return renderHomeSidebar();
  }
}

function baseSidebar(title, createAction, body, bottom = true) {
  return `<aside class="context-sidebar">
    <div class="side-title-row"><div class="side-title">${title}</div>${createAction ? `<button class="icon-btn" onclick="${createAction}">＋</button>` : ''}</div>
    ${body}
    ${bottom ? `<div class="side-bottom"><button class="customize" onclick="toast('Customize sidebar placeholder')">⇵ Customize Sidebar</button></div>` : ''}
  </aside>`;
}

function renderHomeSidebar() {
  return baseSidebar('Home', "toast('Quick create menu opened')", `
    <div class="side-nav">
      ${sideItem('Inbox', '▣', state.module==='home', () => '')}
      ${sideItem('Assigned Comments', '☟')}
      ${sideItem('My Tasks', '♙')}
      ${sideItem('More', '⋯')}
    </div>
    <div class="hr"></div>
    <div class="side-section">AI Chats</div>
    <div class="side-item" onclick="setModule('ai')"><span>＋</span><span class="label">Ask, Build, Create</span></div>
    <div class="side-section">Spaces <button class="icon-btn flat" style="float:right;margin-top:-6px" onclick="toast('New Space placeholder')">＋</button></div>
    ${renderSpacesTree(false)}
  `);
}

function renderSpacesSidebar() {
  return baseSidebar('Spaces', "toast('New Space placeholder')", `
    ${renderSpacesTree(true)}
    <div class="tree-line" onclick="toast('New Space placeholder')"><span>＋</span><span>New Space</span></div>
  `);
}

function renderFormsSidebar() {
  return baseSidebar('Forms', "openFormBuilder()", `
    <div class="side-nav">
      <div class="side-item active" onclick="formBuilderOpen=false; render()"><span>☑</span><span class="label">All Forms</span></div>
      <div class="side-item"><span class="avatar small purple">A</span><span class="label">My Forms</span></div>
    </div>
    <div class="hr"></div>
    <div class="side-section">Favorites</div>
    <div class="favorite-card"><div>⭐<br/>Star a Form to see it here</div></div>
  `);
}

function renderDashboardSidebar() {
  return baseSidebar('Dashboards', "toast('Dashboard create menu opened')", `
    <div class="side-nav">
      <div class="side-item active"><span>▥</span><span class="label">All Dashboards</span></div>
      <div class="side-item"><span class="avatar small purple">A</span><span class="label">My Dashboards</span></div>
      <div class="side-item"><span>♧</span><span class="label">Shared with me</span></div>
      <div class="side-item"><span>🔒</span><span class="label">Private</span></div>
    </div>
    <div class="hr"></div>
    <div class="side-section">Favorites</div>
    <div class="favorite-card"><div>⭐<br/>Star a Dashboard to see it here</div></div>
  `);
}

function renderAISidebar() {
  return baseSidebar('AI', "runAISuggest('Create Agent')", `
    <div class="side-nav">
      <div class="side-item active"><span>✽</span><span class="label">Ask or Create</span></div>
    </div>
    <div class="side-section">Super Agents</div>
    <div class="side-item" onclick="runAISuggest('Create Agent')"><span>👓</span><span class="label">Create Agent</span></div>
    <div class="side-item"><span>🤖</span><span class="label">All Agents</span></div>
    <div class="side-item"><span class="avatar small purple">A</span><span class="label">My Agents</span></div>
    <div class="side-item"><span>◷</span><span class="label">Activity</span></div>
    <div style="height: 455px"></div>
    <div class="side-item"><span>✽</span><span class="label">Connections</span></div>
    <div class="ai-credits"><div><span class="credit-dot"></span>50<br/><span>AI uses</span></div><div><span class="credit-dot"></span>1.5k<br/><span>Credits left</span></div></div>
  `, false);
}

function renderPlannerSidebar() {
  return baseSidebar('Planner', "toast('Add event/task')", `
    <div class="side-nav">
      <div class="side-item active"><span>▣</span><span>Today</span></div>
      <div class="side-item"><span>☰</span><span>Upcoming</span></div>
      <div class="side-item"><span>◷</span><span>Focus Blocks</span></div>
      <div class="side-item"><span>✽</span><span>AI Schedule</span></div>
    </div>
    <div class="hr"></div>
    <div class="side-section">Calendars</div>
    <div class="side-item"><span>🟣</span><span>Work Tasks</span></div>
    <div class="side-item"><span>🔵</span><span>Meetings</span></div>
    <div class="side-item"><span>🟢</span><span>Goals</span></div>
  `);
}

function renderTeamsSidebar() {
  return baseSidebar('Teams', "toast('Invite team member')", `
    <div class="side-nav">
      <div class="side-item active"><span>👥</span><span>Teams Hub</span></div>
      <div class="side-item"><span>☷</span><span>Members</span></div>
      <div class="side-item"><span>▥</span><span>Workload</span></div>
      <div class="side-item"><span>✽</span><span>AI Standups</span></div>
    </div>
  `);
}

function renderDocsSidebar() {
  return baseSidebar('Docs', "createDocFromTemplate()", `
    <div class="side-nav">
      <div class="side-item active"><span>▤</span><span>All Docs</span></div>
      <div class="side-item"><span>📘</span><span>Wikis</span></div>
      <div class="side-item"><span>📝</span><span>Notepad</span></div>
      <div class="side-item"><span>⭐</span><span>Favorites</span></div>
    </div>
    <div class="hr"></div>
    <div class="side-section">Collections</div>
    <div class="side-item"><span>📁</span><span>Project Knowledge</span></div>
    <div class="side-item"><span>📁</span><span>SOPs</span></div>
    <div class="side-item"><span>📁</span><span>Decisions</span></div>
  `);
}

function renderWhiteboardSidebar() {
  ensureWhiteboardState();
  return baseSidebar('Whiteboards', "createWhiteboard()", `
    <div class="side-nav">
      <div class="side-item ${state.visualTab==='whiteboard' ? 'active' : ''}" onclick="setVisualTab('whiteboard')"><span>✎</span><span>All Whiteboards</span></div>
      <div class="side-item ${state.visualTab==='mindmap' ? 'active' : ''}" onclick="setVisualTab('mindmap')"><span>🧠</span><span>Mind Maps</span></div>
      <div class="side-item ${state.visualTab==='canvas' ? 'active' : ''}" onclick="setVisualTab('canvas')"><span>▧</span><span>Canvas</span></div>
      <div class="side-item"><span>⭐</span><span>Favorites</span></div>
    </div>
    <div class="hr"></div>
    <div class="side-section">Boards</div>
    ${(state.whiteboards||[]).map(w=>`<div class="side-item ${state.selectedWhiteboard===w.id?'active':''}" onclick="selectWhiteboard('${w.id}')"><span>${w.icon||'✎'}</span><span class="label">${escapeHtml(w.name)}</span></div>`).join('')}
  `);
}

function renderGoalsSidebar() {
  return baseSidebar('Goals', "toast('New goal')", `
    <div class="side-nav">
      <div class="side-item active"><span>♕</span><span>All Goals</span></div>
      <div class="side-item"><span>🎯</span><span>OKRs</span></div>
      <div class="side-item"><span>📊</span><span>Scorecards</span></div>
      <div class="side-item"><span>⭐</span><span>Favorites</span></div>
    </div>
  `);
}

function renderClipsSidebar() {
  return baseSidebar('Clips', "toast('Record clip placeholder')", `
    <div class="side-nav">
      <div class="side-item active"><span>▰</span><span>All Clips</span></div>
      <div class="side-item"><span>🎙</span><span>Transcripts</span></div>
      <div class="side-item"><span>🐞</span><span>Bug Reports</span></div>
    </div>
  `);
}

function renderMoreSidebar() {
  return baseSidebar('More', "toast('More apps')", `
    <div class="side-nav">
      <div class="side-item" onclick="setModule('dashboards')"><span>▥</span><span>Reports</span></div>
      <div class="side-item" onclick="setModule('automations')"><span>⚡</span><span>Automations</span></div>
      <div class="side-item"><span>🔌</span><span>Integrations</span></div>
      <div class="side-item"><span>🔐</span><span>Admin & Security</span></div>
      <div class="side-item" onclick="showDataLayerStatus()"><span>◉</span><span>Data/Auth Status</span></div>
      <div class="side-item" onclick="resetDemoData()"><span>↺</span><span>Reset demo data</span></div>
    </div>
  `);
}

function renderInviteSidebar() {
  return baseSidebar('Invite', "toast('Invite sent placeholder')", `
    <div class="side-section">Collaborate</div>
    <p style="padding:0 7px;color:var(--muted);line-height:1.5">Invite teammates, guests, and clients with controlled access to Spaces, Projects, Dashboards, Docs, and Forms.</p>
    <button class="btn-primary" style="margin:8px 7px" onclick="toast('Invite modal placeholder')">Invite people</button>
  `);
}

function renderUpgradeSidebar() {
  return baseSidebar('Upgrade', null, `
    <div class="favorite-card" style="height:160px"><div><b>WorkOS Pro</b><br/><br/>Automations, AI Agents, dashboards, guests, and enterprise admin.</div></div>
    <button class="btn-primary" style="margin:8px 7px" onclick="toast('Upgrade placeholder')">Upgrade</button>
  `);
}

function sideItem(label, icon, active=false) {
  return `<div class="side-item ${active ? 'active' : ''}"><span>${icon}</span><span class="label">${label}</span></div>`;
}

function renderSpacesTree(showCounts=true) {
  const p1Count = state.tasks.filter(t => t.projectId === 'p1').length;
  const p2Count = state.tasks.filter(t => t.projectId === 'p2').length;
  return `<div class="tree">
    <div class="tree-line ${state.module === 'spaces' && !state.selectedProject ? 'active' : ''}"><span>⚙</span><span>All Tasks - ${escapeHtml(state.workspace.name).slice(0, 23)}...</span></div>
    <div class="tree-line"><span>👥</span><span>Team Space</span><span class="count">＋</span></div>
    <div class="tree-line indent-1"><span>📁</span><span>Projects</span></div>
    <div class="tree-line indent-2 ${state.selectedProject==='p1' ? 'active' : ''}" onclick="selectProject('p1')"><span>☑</span><span>Project 1</span>${showCounts ? `<span class="count">${p1Count}</span>` : ''}</div>
    <div class="tree-line indent-2 ${state.selectedProject==='p2' ? 'active' : ''}" onclick="selectProject('p2')"><span>☑</span><span>Project 2</span>${showCounts ? `<span class="count">${p2Count}</span>` : ''}</div>
    <div class="tree-line indent-2" onclick="setModule('docs')"><span>📄</span><span>Project Notes</span></div>
  </div>`;
}

function selectProject(id) {
  state.module = 'spaces';
  state.selectedProject = id;
  render();
}

function renderMain() {
  switch (state.module) {
    case 'home': return renderHome();
    case 'spaces': return renderSpacesMain();
    case 'forms': return renderFormsMain();
    case 'dashboards': return renderDashboardMain();
    case 'ai': return renderAIMain();
    case 'planner': return renderPlannerMain();
    case 'teams': return renderTeamsMain();
    case 'docs': return renderDocsMain();
    case 'whiteboards': return renderWhiteboardsMain();
    case 'goals': return renderGoalsMain();
    case 'clips': return renderClipsMain();
    case 'more': return renderMoreMain();
    case 'automations': return renderMoreMain();
    case 'invite': return renderInviteMain();
    case 'upgrade': return renderUpgradeMain();
    default: return renderHome();
  }
}

function renderHome() {
  const items = state.notifications.filter(n => n.tab === activeHomeTab && !n.read);
  return `<div class="content wide">
    <div class="project-head" style="top:51px;padding-top:0">
      <div class="tabs" style="height:64px">
        ${['Primary','Other','Later','Cleared'].map(tab => `<button class="tab ${activeHomeTab===tab ? 'active' : ''}" onclick="setHomeTab('${tab}')">${tabIcon(tab)} ${tab}</button>`).join('')}
      </div>
    </div>
    <div class="view-toolbar"><div><button class="pill-control">☰ Filter</button></div><div class="toolbar-right"><button class="icon-btn flat">⚙</button><button class="btn-secondary btn-small" onclick="clearNotifications()">✓ Clear all</button></div></div>
    ${items.length ? `<div class="task-table-wrap" style="max-width:900px">
      <div class="section-title"><h2>${activeHomeTab}</h2><button class="btn-primary" onclick="setModule('ai')">Ask AI to prioritize</button></div>
      ${items.map(n => `<div class="report-card" style="margin-bottom:10px"><div style="display:flex;justify-content:space-between;gap:20px"><div><b>${escapeHtml(n.title)}</b><p style="margin:4px 0 0;color:var(--muted)">${n.source} • actionable update</p></div><div><button class="btn-secondary btn-small" onclick="markNotificationRead('${n.id}')">Clear</button></div></div></div>`).join('')}
    </div>` : renderHomeEmpty()}
    ${state.helper ? renderFeedbackWidget() : ''}
  </div>`;
}

function renderHomeEmpty() {
  return `<div class="empty-center">
    <div class="big-icon">♙+</div>
    <h2>Looking to collaborate?</h2>
    <div>Collaboration is one invite away.</div>
    <br/><button class="btn-primary" onclick="setModule('invite')">Invite people</button>
  </div>`;
}

function tabIcon(tab) {
  return { Primary:'▣', Other:'⌁', Later:'◷', Cleared:'✓' }[tab];
}
function setHomeTab(tab) { activeHomeTab = tab; render(); }
function markNotificationRead(id) { const n=state.notifications.find(x=>x.id===id); if(n) n.read=true; toast('Notification cleared'); render(); }
function clearNotifications() { state.notifications.forEach(n => { if(n.tab===activeHomeTab) n.read = true; }); toast('Cleared'); render(); }

function renderSpacesMain() {
  const projectName = getProjectName(state.selectedProject);
  return `<div class="content wide">
    <div class="project-head">
      <div class="project-actions"><button class="btn-ghost btn-small" onclick="setModule('ai')">👓 Agents</button><button class="btn-ghost btn-small" onclick="setModule('more')">⚡ Automate</button><button class="btn-ghost btn-small" onclick="setModule('ai')">✽ AI</button><button class="btn-ghost btn-small" onclick="setModule('invite')">♙ Share</button></div>
      <div class="breadcrumb"><span>👥 Team Space</span><span>/</span><span>📁 Projects</span><span>/</span><strong>☑ ${projectName}</strong><button class="icon-btn flat">☆</button></div>
      <div class="tabs">
        ${viewTab('board','▦ Board')}
        ${viewTab('list','▤ List')}
        ${viewTab('calendar','▣ Calendar')}
        ${viewTab('gantt','▰ Gantt')}
        ${viewTab('table','▥ Table')}
        <button class="tab" onclick="toast('Create custom view placeholder')">＋ View</button>
      </div>
    </div>
    <div class="view-toolbar">
      <div class="toolbar-left"><button class="pill-control active">◉ Status</button><button class="pill-control">⌘</button><button class="pill-control">▥</button></div>
      <div class="toolbar-right"><button class="icon-btn flat">☰</button><button class="pill-control">✓ ×</button><button class="icon-btn flat">⌕</button><button class="icon-btn flat">⚙</button><button class="btn-primary" onclick="quickAddTask()">＋ Task ▾</button></div>
    </div>
    ${renderProjectView()}
    ${state.helper ? renderFeedbackWidget() : ''}
  </div>`;
}

function viewTab(view, label) {
  return `<button class="tab ${state.view===view ? 'active' : ''}" onclick="setView('${view}')">${label}</button>`;
}
function setView(view) { state.view = view; render(); if (view === 'gantt') refreshGanttFromApi(false); }
function getProjectName(id) { return id === 'p2' ? 'Project 2' : 'Project 1'; }
function projectTasks() { return state.tasks.filter(t => t.projectId === state.selectedProject); }
function renderProjectView() {
  if (state.view === 'board') return renderBoardView();
  if (state.view === 'calendar') return renderCalendarView();
  if (state.view === 'gantt') return renderGanttView();
  if (state.view === 'table') return renderTableView();
  return renderListView();
}

const statuses = ['TO DO','IN PROGRESS','BLOCKED','DONE'];
const statusClass = { 'TO DO':'todo', 'IN PROGRESS':'progress', 'BLOCKED':'blocked', 'DONE':'done' };
const statusLabels = { 'TO DO':'TO DO', 'IN PROGRESS':'IN PROGRESS', 'BLOCKED':'BLOCKED', 'DONE':'DONE' };

function renderListView() {
  const tasks = projectTasks();
  return `<div class="task-table-wrap">
    ${statuses.map(st => {
      const group = tasks.filter(t => t.status === st);
      if (!group.length && st !== 'TO DO') return '';
      return `<div class="group-header"><span class="status-dot"></span><span class="status-pill ${statusClass[st]}">${st}</span><span>${group.length}</span></div>
      <table class="task-table">
        <thead><tr><th style="width:28%">Name</th><th>Assignee</th><th>Due date</th><th>Priority</th><th>Status</th><th>Comments</th><th>＋</th></tr></thead>
        <tbody>
          ${group.map(renderTaskRow).join('')}
        </tbody>
      </table>
      ${st === 'TO DO' ? `<div class="add-task-row"><span>＋</span><input id="newTaskInput" placeholder="Add Task" onkeydown="if(event.key==='Enter') addTaskFromInput(this.value)" /></div>` : ''}`;
    }).join('')}
  </div>`;
}

function renderTaskRow(t) {
  return `<tr>
    <td onclick="openTask('${t.id}')"><div class="task-name"><span class="task-check"></span>${escapeHtml(t.name)}</div></td>
    <td><select class="inline-select" onchange="updateTask('${t.id}','assignee',this.value)">${state.members.map(m => `<option value="${m.id}" ${t.assignee===m.id?'selected':''}>${escapeHtml(m.name)}</option>`).join('')}</select></td>
    <td><input class="inline-input" type="date" value="${t.due}" onchange="updateTask('${t.id}','due',this.value)" /></td>
    <td><select class="inline-select priority ${t.priority.toLowerCase()}" onchange="updateTask('${t.id}','priority',this.value)">${['Urgent','High','Normal','Low'].map(p => `<option ${t.priority===p?'selected':''}>${p}</option>`).join('')}</select></td>
    <td><select class="inline-select" onchange="updateTask('${t.id}','status',this.value)">${statuses.map(s => `<option ${t.status===s?'selected':''}>${s}</option>`).join('')}</select></td>
    <td onclick="openTask('${t.id}')">▢ ${t.comments.length}</td>
    <td><button class="icon-btn flat" onclick="openTask('${t.id}')">⋯</button></td>
  </tr>`;
}

function renderBoardView() {
  return `<div class="board-grid">
    ${statuses.map(st => {
      const group = projectTasks().filter(t => t.status === st);
      return `<div class="board-col" data-status="${st}" ondragover="event.preventDefault()" ondrop="dropTask(event, '${st}')">
        <div class="board-col-head"><span class="status-pill ${statusClass[st]}">${st}</span><span>${group.length}</span></div>
        ${group.map(t => `<div class="task-card" draggable="true" ondragstart="dragTask(event, '${t.id}')" onclick="openTask('${t.id}')"><div class="task-card-title">${escapeHtml(t.name)}</div><div class="task-meta"><span class="avatar small ${memberById(t.assignee).avatar}">${memberById(t.assignee).initials}</span><span>${dateShort(t.due)}</span><span class="priority ${t.priority.toLowerCase()}">⚑ ${t.priority}</span><span>▢ ${t.comments.length}</span></div></div>`).join('')}
        <button class="btn-secondary btn-small" style="width:100%" onclick="quickAddTask('${st}')">＋ Add Task</button>
      </div>`;
    }).join('')}
  </div>`;
}

function dragTask(event, id) { event.dataTransfer.setData('taskId', id); }
function dropTask(event, status) { const id = event.dataTransfer.getData('taskId'); updateTask(id, 'status', status); toast(`Moved to ${status}`); }

function renderCalendarView() {
  const days = ['Mon 6','Tue 7','Wed 8','Thu 9','Fri 10','Sat 11','Sun 12'];
  return `<div class="calendar-grid">
    ${days.map((d, idx) => {
      const dayTasks = projectTasks().filter((t,i) => (new Date(t.due).getDate()+i) % 7 === idx);
      return `<div class="calendar-day"><h4>${d}</h4>${dayTasks.map(t => `<div class="cal-task" onclick="openTask('${t.id}')">${escapeHtml(t.name)}</div>`).join('')}</div>`;
    }).join('')}
  </div>`;
}

function renderGanttView() {
  ensureGanttState();
  const data = (lastGanttDataset && lastGanttDataset.projectId === state.selectedProject) ? lastGanttDataset : computeLocalGanttDataset(state.selectedProject);
  const timeline = data.timeline || { start:'2026-07-04', end:'2026-07-14', days:10 };
  const ticks = ganttTicks(timeline.start, timeline.days);
  const tasks = data.tasks || [];
  const dependencies = data.dependencies || [];
  const risks = data.risks || [];
  const metrics = data.metrics || {};
  const taskOptions = projectTasks().map(t => `<option value="${t.id}">${escapeHtml(t.name)}</option>`).join('');
  return `<div class="gantt-command-center">
    <div class="gantt-hero">
      <div><span class="badge purple">v0.7 Critical Path</span><h2>Gantt that keeps up when plans don't</h2><p>Set dependencies, track critical path, cascade schedule changes, and let AI flag delay risks before they spread.</p></div>
      <div class="gantt-actions"><button class="btn-primary" onclick="recalculateGantt()">✦ Recalculate critical path</button><button class="btn-secondary" onclick="createGanttBaseline()">Capture baseline</button><button class="btn-secondary" onclick="refreshGanttFromApi()">Refresh</button></div>
    </div>
    <div class="gantt-metrics">
      ${ganttMetricCard('Tasks', metrics.taskCount ?? tasks.length, 'Current project scope')}
      ${ganttMetricCard('Dependencies', metrics.dependencyCount ?? dependencies.length, 'Finish-to-start links')}
      ${ganttMetricCard('Critical path', metrics.criticalTasks ?? tasks.filter(t=>t.criticalPath).length, 'Tasks driving finish date')}
      ${ganttMetricCard('Risks', metrics.riskCount ?? risks.length, `${metrics.conflictCount || 0} conflicts • Finish ${metrics.endDate || timeline.end}`)}
    </div>
    <div class="gantt-grid-card">
      <div class="gantt-table-head"><div>Task / owner</div><div class="gantt-timescale">${ticks.map(x=>`<span>${x}</span>`).join('')}</div><div>Schedule controls</div></div>
      ${tasks.map(t => renderGanttTaskRow(t, timeline)).join('')}
    </div>
    <div class="gantt-lower-grid">
      <div class="gantt-panel"><div class="section-title"><h3>Dependency editor</h3><button class="btn-secondary btn-small" onclick="addGanttDependencyFromControls()">＋ Link</button></div>
        <div class="dependency-controls"><select id="ganttPred">${taskOptions}</select><span>→</span><select id="ganttSucc">${taskOptions}</select><select id="ganttLag"><option value="0">0 day lag</option><option value="1">1 day lag</option><option value="2">2 day lag</option></select></div>
        ${dependencies.length ? dependencies.map(renderDependencyRow).join('') : '<p class="muted">No dependencies yet. Link two tasks to drive the critical path.</p>'}
      </div>
      <div class="gantt-panel"><div class="section-title"><h3>AI delay watch</h3><button class="btn-secondary btn-small" onclick="setModule('planner')">Plan recovery</button></div>
        ${risks.length ? risks.map(r => `<div class="risk-row ${r.level || 'medium'}"><b>${escapeHtml(r.title)}</b><p>${escapeHtml(r.recommendation || 'Review schedule and owner capacity.')}</p>${r.taskId ? `<button class="btn-secondary btn-small" onclick="openTask('${r.taskId}')">Open task</button>` : ''}</div>`).join('') : '<div class="risk-row low"><b>No critical schedule risks found</b><p>Dependencies and critical path are currently aligned.</p></div>'}
      </div>
    </div>
  </div>`;
}

function renderTableView() {
  return `<div class="table-view-card">
    <table class="task-table">
      <thead><tr><th>Name</th><th>Owner</th><th>Status</th><th>Progress</th><th>Estimate</th><th>Tracked</th><th>Billable</th><th>Tags</th></tr></thead>
      <tbody>${projectTasks().map(t => `<tr><td onclick="openTask('${t.id}')"><b>${escapeHtml(t.name)}</b></td><td>${memberById(t.assignee).name}</td><td><select class="inline-select" onchange="updateTask('${t.id}','status',this.value)">${statuses.map(s => `<option ${t.status===s?'selected':''}>${s}</option>`).join('')}</select></td><td><input class="inline-input" type="number" min="0" max="100" value="${t.progress}" onchange="updateTask('${t.id}','progress',Number(this.value))" />%</td><td>${t.estimate}h</td><td>${t.tracked}h</td><td>${t.billable ? 'Yes' : 'No'}</td><td>${t.tags.join(', ')}</td></tr>`).join('')}</tbody>
    </table>
  </div>`;
}

function addTaskFromInput(value, status='TO DO') {
  const name = (value || '').trim();
  if (!name) return;
  state.tasks.push({ id: uid(), projectId: state.selectedProject, name, assignee: 'adrian', due: '2026-07-12', priority: 'Normal', status, comments: [], estimate: 1, tracked: 0, billable: false, tags: ['New'], progress: 0, description: '', start: '2026-07-08', duration: 2, critical: false });
  toast('Task created');
  render();
}
function quickAddTask(status='TO DO') {
  const name = prompt('Task name');
  if (name) addTaskFromInput(name, status);
}
function updateTask(id, field, value) {
  const t = state.tasks.find(x => x.id === id);
  if (!t) return;
  t[field] = value;
  if (field === 'status') {
    t.progress = value === 'DONE' ? 100 : value === 'IN PROGRESS' ? Math.max(t.progress, 35) : value === 'BLOCKED' ? Math.max(t.progress, 20) : t.progress;
  }
  saveState();
  render();
}
function openTask(id) { selectedTaskId = id; render(); }
function closeTaskDrawer() { selectedTaskId = null; render(); }

function renderTaskDrawer() {
  const t = state.tasks.find(x => x.id === selectedTaskId);
  if (!t) return `<section class="task-drawer"></section>`;
  return `<section class="task-drawer show">
    <div class="drawer-head"><div class="drawer-title">${escapeHtml(t.name)}</div><button class="icon-btn flat" onclick="closeTaskDrawer()">×</button></div>
    <div class="drawer-body">
      <div class="field-grid">
        <div class="field-label">Assignee</div><div><select class="inline-select" onchange="updateTask('${t.id}','assignee',this.value)">${state.members.map(m => `<option value="${m.id}" ${t.assignee===m.id?'selected':''}>${m.name}</option>`).join('')}</select></div>
        <div class="field-label">Status</div><div><select class="inline-select" onchange="updateTask('${t.id}','status',this.value)">${statuses.map(s => `<option ${t.status===s?'selected':''}>${s}</option>`).join('')}</select></div>
        <div class="field-label">Due date</div><div><input class="inline-input" type="date" value="${t.due}" onchange="updateTask('${t.id}','due',this.value)" /></div>
        <div class="field-label">Priority</div><div><select class="inline-select" onchange="updateTask('${t.id}','priority',this.value)">${['Urgent','High','Normal','Low'].map(p => `<option ${t.priority===p?'selected':''}>${p}</option>`).join('')}</select></div>
        <div class="field-label">Time</div><div>${t.tracked}h tracked / ${t.estimate}h estimate ${t.billable ? '<span class="badge green">Billable</span>' : '<span class="badge">Non-billable</span>'}</div>
        <div class="field-label">Tags</div><div>${t.tags.map(tag => `<span class="badge">${escapeHtml(tag)}</span>`).join(' ')}</div>
      </div>
      <h3>Description</h3>
      <textarea class="textarea" onchange="updateTask('${t.id}','description',this.value)">${escapeHtml(t.description || '')}</textarea>
      <div class="section-title"><h2>AI actions</h2><div><button class="btn-secondary btn-small" onclick="aiTaskSummary('${t.id}')">Summarize</button><button class="btn-primary btn-small" onclick="aiCreateSubtasks('${t.id}')">Create subtasks</button></div></div>
      <div class="report-card"><b>AI risk check:</b> ${t.status === 'BLOCKED' ? 'This item is blocked and on the critical path. Recommend escalation and owner confirmation.' : 'No major risk detected from current task state.'}</div>
      <div class="section-title"><h2>Comments</h2></div>
      ${t.comments.map(c => `<div class="comment"><div class="by">${escapeHtml(c.by)}</div>${escapeHtml(c.text)}</div>`).join('') || '<p style="color:var(--muted)">No comments yet.</p>'}
      <div class="comment-box"><input id="commentInput" placeholder="Add a comment or @mention an agent" onkeydown="if(event.key==='Enter') addComment('${t.id}', this.value)" /><button class="btn-primary" onclick="addComment('${t.id}', $('#commentInput').value)">Send</button></div>
    </div>
  </section>`;
}

function addComment(id, text) {
  const t = state.tasks.find(x => x.id === id);
  const val = (text || '').trim();
  if (!t || !val) return;
  t.comments.push({ by: 'Adrian Francis', text: val });
  toast('Comment added');
  render();
}
function aiTaskSummary(id) { const t=state.tasks.find(x=>x.id===id); toast(`AI summary generated for ${t.name}`); }
function aiCreateSubtasks(id) { const t=state.tasks.find(x=>x.id===id); toast(`AI drafted 4 subtasks for ${t.name}`); }

function computeLocalReportDataset() {
  const filter = state.reportFilter || 'all';
  const tasks = filter === 'project1' ? state.tasks.filter(t => t.projectId === 'p1') : filter === 'project2' ? state.tasks.filter(t => t.projectId === 'p2') : state.tasks;
  const done = tasks.filter(t => t.status === 'DONE');
  const open = tasks.filter(t => t.status !== 'DONE');
  const blocked = tasks.filter(t => t.status === 'BLOCKED');
  const tracked = tasks.reduce((sum,t) => sum + Number(t.tracked || 0), 0);
  const estimate = tasks.reduce((sum,t) => sum + Number(t.estimate || 0), 0);
  const billable = tasks.filter(t => t.billable).reduce((sum,t) => sum + Number(t.tracked || 0), 0);
  const byStatus = statuses.reduce((acc,s) => ({...acc, [s]: tasks.filter(t=>t.status===s).length}), {});
  const byPriority = ['Urgent','High','Normal','Low'].reduce((acc,p) => ({...acc, [p]: tasks.filter(t=>t.priority===p).length}), {});
  const byAssignee = state.members.map(m => {
    const owned = tasks.filter(t => t.assignee === m.id);
    return { id:m.id, name:m.name, tasks: owned.length, done: owned.filter(t=>t.status==='DONE').length, tracked: owned.reduce((s,t)=>s+Number(t.tracked||0),0), estimate: owned.reduce((s,t)=>s+Number(t.estimate||0),0) };
  });
  const risks = tasks.filter(t => t.status === 'BLOCKED' || (t.critical && t.status !== 'DONE'));
  const health = blocked.length || risks.length >= 2 ? 'At Risk' : 'On Track';
  return {
    schema: 'local-reporting-v0.5',
    generated_at: new Date().toISOString(),
    summary: { total_tasks: tasks.length, open_tasks: open.length, completed_tasks: done.length, blocked_tasks: blocked.length, billable_hours: Number(billable.toFixed(1)), tracked_hours: Number(tracked.toFixed(1)), estimate_hours: Number(estimate.toFixed(1)), completion_pct: tasks.length ? Math.round(done.length/tasks.length*100) : 0, utilization_pct: estimate ? Math.round(tracked/estimate*100) : 0, health },
    by_status: byStatus,
    by_priority: byPriority,
    by_assignee: byAssignee,
    work_table: tasks,
    blockers: blocked,
    risks,
    forms: state.forms,
    goals: state.goals,
  };
}

function dashboardDataset() {
  if (lastReportDataset?.dataset) return lastReportDataset.dataset;
  return computeLocalReportDataset();
}

function renderDashboardMain() {
  if (!state.dashboards.length) return renderDashboardTemplates();
  const dataset = dashboardDataset();
  const summary = dataset.summary;
  const cards = state.reportCards && state.reportCards.length ? state.reportCards : seedState.reportCards;
  return `<div class="content wide">
    <div class="section-title"><div><h2>Executive PMO Dashboard</h2><p style="margin:4px 0 0;color:var(--muted)">v0.5 intake automation engine: live cards, drill-downs, filters, and dashboard actions that update real work.</p></div><div><button class="btn-secondary" onclick="renderDashboardTemplatesOnly()">Templates</button> <button class="btn-secondary" onclick="refreshReportDataset()">⟳ Refresh reports</button> <button class="btn-primary" onclick="addReportCard()">＋ Add Card</button></div></div>
    <div class="report-toolbar">
      <button class="pill-control ${state.reportFilter==='all'?'active':''}" onclick="setReportFilter('all')">All work</button>
      <button class="pill-control ${state.reportFilter==='project1'?'active':''}" onclick="setReportFilter('project1')">Project 1</button>
      <button class="pill-control ${state.reportFilter==='project2'?'active':''}" onclick="setReportFilter('project2')">Project 2</button>
      <span class="report-status">${reportStatusText} • ${new Date(dataset.generated_at).toLocaleTimeString()}</span>
    </div>
    <div class="cards-grid report-kpis">
      ${renderReportCard(cards.find(c=>c.metric==='open_tasks') || {title:'Open Tasks', metric:'open_tasks'}, dataset)}
      ${renderReportCard(cards.find(c=>c.metric==='blocked_tasks') || {title:'Blocked Work', metric:'blocked_tasks'}, dataset)}
      ${renderReportCard(cards.find(c=>c.metric==='billable_hours') || {title:'Billable Hours', metric:'billable_hours'}, dataset)}
      ${renderReportCard(cards.find(c=>c.metric==='health') || {title:'Project Health', metric:'health'}, dataset)}
    </div>
    <div class="section-title"><h2>Custom reports you can actually work from</h2><button class="btn-secondary" onclick="setModule('ai')">Ask AI for update</button></div>
    <div class="dashboard-grid v040">
      <div class="report-card">
        <div class="report-card-head"><h3>Campaign performance</h3><span class="badge green">Actionable</span></div>
        <div class="chart-bars">${[summary.completion_pct, 78, Math.max(18, summary.utilization_pct), 84, 52, 92].map(v => `<div class="chart-bar" style="height:${Math.min(100,Math.max(12,v))}%">${v}</div>`).join('')}</div>
        <p style="color:var(--muted)">Throughput, utilization, and completion are tied to source tasks. Use the controls below to update work without switching tools.</p>
        ${renderInlineTaskActionTable(dataset.work_table.filter(t => t.tags.includes('Dashboard') || t.tags.includes('Forms') || t.projectId==='p1').slice(0,6))}
      </div>
      <div class="report-card">
        <div class="report-card-head"><h3>AI Project Health Card</h3><span class="badge ${summary.health==='At Risk'?'warn':'green'}">${summary.health}</span></div>
        <div class="donut" style="background: conic-gradient(var(--primary) 0 ${summary.completion_pct}%, #e9e7ef ${summary.completion_pct}% 100%)"><div class="donut-inner">${summary.completion_pct}%</div></div>
        <p style="color:var(--muted)"><b>AI finding:</b> ${summary.health === 'At Risk' ? `There are ${summary.blocked_tasks} blocked items and ${dataset.risks.length} schedule risks. Escalate critical path tasks today.` : 'Portfolio looks on track. Keep focus on upcoming due dates and billable accuracy.'}</p>
        <div>${sourcePills(dataset.risks.slice(0,4).map(t=>t.name))}</div><br/>
        <button class="btn-primary" onclick="runAISuggest('Status Report')">Generate status report</button>
      </div>
      <div class="report-card">
        <div class="report-card-head"><h3>Team productivity</h3><span class="badge">Live rollup</span></div>
        ${dataset.by_assignee.map(m => {
          const pct = Math.round((m.done/(m.tasks||1))*100);
          return `<div class="team-rollup"><div style="display:flex;justify-content:space-between"><b>${escapeHtml(m.name)}</b><span>${m.tasks} tasks • ${Number(m.tracked).toFixed(1)}h</span></div><div class="progress"><span style="width:${pct}%"></span></div></div>`;
        }).join('')}
      </div>
      <div class="report-card">
        <div class="report-card-head"><h3>Billable hours</h3><span class="badge green">${summary.billable_hours}h</span></div>
        ${dataset.work_table.filter(t=>t.billable).slice(0,6).map(t => `<div class="billable-row"><span onclick="openTask('${t.id}')">${escapeHtml(t.name)}</span><b>${t.tracked}h</b><button class="btn-secondary btn-small" onclick="dashboardAction('${t.id}','toggle_billable')">Toggle</button></div>`).join('')}
        <br/><button class="btn-secondary" onclick="setModule('planner')">Plan remaining work</button>
      </div>
      <div class="report-card wide-card">
        <div class="report-card-head"><h3>Drill-down: Work by status</h3><span class="badge">Click to filter</span></div>
        <div class="status-drill-grid">${Object.entries(dataset.by_status).map(([name,count]) => `<button class="status-drill" onclick="drilldownReport('status:${name}')"><span class="status-pill ${statusClass[name]||''}">${name}</span><b>${count}</b></button>`).join('')}</div>
      </div>
      <div class="report-card wide-card">
        <div class="report-card-head"><h3>Risk and blocker action queue</h3><span class="badge warn">${dataset.risks.length} risks</span></div>
        ${renderInlineTaskActionTable(dataset.risks.slice(0,8))}
      </div>
    </div>
    ${state.aiPromo ? renderBrainPromoWidget() : ''}
  </div>`;
}

function renderReportCard(card, dataset) {
  const s = dataset.summary;
  const metricMap = {
    open_tasks: [s.open_tasks, 'Update status directly from report'],
    blocked_tasks: [s.blocked_tasks, s.blocked_tasks ? 'Needs escalation' : 'No blockers'],
    billable_hours: [Number(s.billable_hours).toFixed(1), `${Math.round((s.billable_hours/(s.tracked_hours||1))*100)}% of tracked time`],
    health: [s.health, `${s.completion_pct}% complete • ${dataset.risks.length} risks`],
  };
  const [value, trend] = metricMap[card.metric] || [s.total_tasks, 'Live metric'];
  const tone = card.metric === 'blocked_tasks' && Number(value) > 0 ? 'red' : card.metric === 'health' && value === 'At Risk' ? 'red' : 'green';
  return `<div class="kpi-card report-card-live" onclick="drilldownReport('${card.metric === 'health' ? 'open_tasks' : card.metric}')"><div class="label">${escapeHtml(card.title)}</div><div class="value">${value}</div><div class="trend ${tone==='red'?'red':''}">${trend}</div><div class="card-actions"><button class="btn-secondary btn-small" onclick="event.stopPropagation(); drilldownReport('${card.metric === 'health' ? 'open_tasks' : card.metric}')">Drill down</button></div></div>`;
}

function setReportFilter(filter) { state.reportFilter = filter; lastReportDataset = null; toast(`Report filter: ${filter}`); render(); }

function addReportCard() {
  const title = prompt('Report card title', 'Custom Risk Card');
  if (!title) return;
  const metric = prompt('Metric: open_tasks, blocked_tasks, billable_hours, health, by_status, by_assignee', 'blocked_tasks') || 'open_tasks';
  state.reportCards = state.reportCards || [];
  state.reportCards.push({ id: uid(), title, type: metric.includes('by_') ? 'chart' : 'kpi', metric });
  toast('Report card added');
  render();
}

async function dashboardAction(taskId, action, value=null) {
  const task = state.tasks.find(t => t.id === taskId);
  if (!task) return;
  if (apiOnline) {
    try {
      const response = await fetch(`${API_BASE}/reports/actions`, { method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() }, body: JSON.stringify({ task_id: taskId, action, value, comment: value }) });
      if (response.ok) {
        const data = await response.json();
        if (data.state) { state = { ...state, ...data.state }; localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
        lastReportDataset = data.dataset ? { dataset: data.dataset } : null;
        toast('Dashboard action saved through API');
        render();
        return;
      }
    } catch (error) { console.warn('Report action API failed; applying locally', error); }
  }
  if (action === 'set_status') updateTask(taskId, 'status', value);
  if (action === 'assign') updateTask(taskId, 'assignee', value);
  if (action === 'set_due') updateTask(taskId, 'due', value);
  if (action === 'toggle_billable') updateTask(taskId, 'billable', !task.billable);
  if (action === 'add_comment') addComment(taskId, value || 'Dashboard follow-up');
}

async function drilldownReport(metric) {
  if (apiOnline) {
    try {
      const response = await fetch(`${API_BASE}/reports/drilldown?metric=${encodeURIComponent(metric)}`, { headers: authHeaders(), cache:'no-store' });
      if (response.ok) {
        const data = await response.json();
        toast(`${data.count} source records for ${metric}`);
        if (data.tasks && data.tasks[0]) { state.module='spaces'; state.selectedProject=data.tasks[0].projectId || 'p1'; selectedTaskId=data.tasks[0].id; render(); }
        return;
      }
    } catch (error) { console.warn('Drilldown API failed', error); }
  }
  const dataset = computeLocalReportDataset();
  let tasks = dataset.work_table;
  if (metric === 'open_tasks') tasks = tasks.filter(t=>t.status!=='DONE');
  if (metric === 'blocked_tasks') tasks = tasks.filter(t=>t.status==='BLOCKED');
  if (metric === 'billable_hours') tasks = tasks.filter(t=>t.billable);
  if (metric.startsWith('status:')) tasks = tasks.filter(t=>t.status===metric.split(':')[1]);
  toast(`${tasks.length} source records for ${metric}`);
  if (tasks[0]) { state.module='spaces'; state.selectedProject=tasks[0].projectId; selectedTaskId=tasks[0].id; render(); }
}

function renderDashboardTemplatesOnly(){ state.dashboards=[]; render(); }
function renderDashboardTemplates() {
  return `<div class="content wide">
    <div class="template-wrap"><h1>Choose a Dashboard template</h1><p>Get started with a Dashboard template or create a custom Dashboard to fit your exact needs.</p>
      <div class="template-grid">
        ${templateCard('▧','Simple Dashboard','Manage and prioritize tasks','blue', 'createDashboard()')}
        ${templateCard('✽','AI Team Center','View team activity with AI','purple', 'createDashboard()')}
        ${templateCard('⏱','Time Tracking','View and report on time tracking metrics','green', 'createDashboard()', 'Business')}
        ${templateCard('☑','Project Management','Analyze project progress and metrics','blue', 'createDashboard()', 'Business')}
        ${templateCard('✽','AI Personal Center','Improve your performance with AI cards','purple', 'createDashboard()')}
        ${templateCard('＋','Start from scratch','Create your own live reporting workspace','gray', 'createDashboard()')}
      </div>
    </div>
    ${state.aiPromo ? renderBrainPromoWidget() : ''}
  </div>`;
}
function createDashboard() { state.dashboards.push({ id: uid(), name:'Executive PMO Dashboard', private:false, favorite:true }); if (!state.reportCards) state.reportCards = structuredClone(seedState.reportCards); toast('Dashboard created'); render(); }
function kpi(label, value, trend, tone='') { return `<div class="kpi-card"><div class="label">${label}</div><div class="value">${value}</div><div class="trend ${tone==='red'?'red':''}">${trend}</div></div>`; }
function renderInlineTaskActionTable(tasks) {
  if (!tasks.length) return `<div class="empty-mini">No source records match this report.</div>`;
  return `<table class="inline-table"><thead><tr><th>Task</th><th>Status</th><th>Owner</th><th>Due</th><th></th></tr></thead><tbody>${tasks.map(t => `<tr><td onclick="openTask('${t.id}')"><b>${escapeHtml(t.name)}</b><br/><span class="muted-mini">${t.tags.join(', ')}</span></td><td><select class="inline-select" onchange="dashboardAction('${t.id}','set_status',this.value)">${statuses.map(s => `<option ${t.status===s?'selected':''}>${s}</option>`).join('')}</select></td><td><select class="inline-select" onchange="dashboardAction('${t.id}','assign',this.value)">${state.members.map(m => `<option value="${m.id}" ${t.assignee===m.id?'selected':''}>${escapeHtml(m.name)}</option>`).join('')}</select></td><td><input class="inline-input" type="date" value="${t.due}" onchange="dashboardAction('${t.id}','set_due',this.value)" /></td><td><button class="btn-secondary btn-small" onclick="openTask('${t.id}')">Open</button></td></tr>`).join('')}</tbody></table>`;
}

function renderFormsMain() {
  if (formBuilderOpen) return renderFormBuilder();
  return `<div class="content wide">
    <div class="template-wrap"><h1>Choose a Form template</h1><p>Create forms to kick off projects, collect feedback, and supercharge your productivity.</p>
      <div class="template-grid">
        ${templateCard('🎛','Feedback Form','Survey and collect feedback','green', 'openFormBuilder()')}
        ${templateCard('📋','Project Intake','Streamline new project requests','pink', 'openFormBuilder()')}
        ${templateCard('🧺','Order Form','Capture and process client orders','purple', 'openFormBuilder()')}
        ${templateCard('👤','Job Application','Accept and review applications for open roles','orange', 'openFormBuilder()')}
        ${templateCard('🧾','IT Requests','Triage and prioritize IT service requests','blue', 'openFormBuilder()')}
        ${templateCard('＋','Start from scratch','Build a connected form that creates work','gray', 'openFormBuilder()')}
      </div>
    </div>
    ${state.aiPromo ? renderBrainPromoWidget() : ''}
  </div>`;
}

function openFormBuilder() { formBuilderOpen = true; state.module = 'forms'; render(); }
function renderFormBuilder() {
  return `<div class="content">
    <div class="section-title"><div><h2>Project Intake Form</h2><p style="margin:4px 0 0;color:var(--muted)">Responses create tasks in Team Space / Projects / Project 1 and trigger AI analysis.</p></div><div><button class="btn-secondary" onclick="formBuilderOpen=false;render()">Templates</button><button class="btn-primary" onclick="submitFormDemo()">Submit test response</button></div></div>
    <div class="form-builder">
      <div class="report-card"><h3>Fields</h3>
        ${['Project name','Requester','Department','Priority','Desired due date','Business objective','Attachment'].map((f,i) => `<div class="side-item"><span>${i+1}</span><span>${f}</span></div>`).join('')}
        <div class="hr"></div><button class="btn-secondary" onclick="toast('Field added')">＋ Add Field</button>
        <button class="btn-primary" style="margin-left:8px" onclick="toast('AI suggested 3 form improvements')">✽ AI Improve</button>
      </div>
      <div class="form-preview">
        <h2>Project Intake</h2><p style="color:var(--muted)">Use this form to centralize new work and create a project kickoff task automatically.</p>
        <div class="form-field"><label>Project name *</label><input id="formProjectName" placeholder="e.g., Launch customer dashboard" /></div>
        <div class="form-field"><label>Requester *</label><input placeholder="Name or email" /></div>
        <div class="form-field"><label>Priority</label><select><option>Normal</option><option>High</option><option>Urgent</option></select></div>
        <div class="form-field"><label>Business objective</label><textarea placeholder="What result should this project deliver?"></textarea></div>
        <button class="btn-primary" onclick="submitFormDemo()">Submit request</button>
      </div>
    </div>
  </div>`;
}
function submitFormDemo() {
  const name = ($('#formProjectName')?.value || 'New intake request from Form').trim();
  state.tasks.push({ id: uid(), projectId: 'p1', name, assignee: 'mira', due: '2026-07-15', priority: 'Normal', status: 'TO DO', comments: [{ by:'AI Intake Agent', text:'AI classified this request as Project Intake and suggested Mira as owner.'}], estimate: 2, tracked: 0, billable: false, tags: ['Intake','AI'], progress: 0, description: 'Created from Project Intake Form.', start: '2026-07-12', duration: 3, critical: false });
  toast('Form submitted → task created');
  state.module = 'spaces';
  state.selectedProject = 'p1';
  state.view = 'list';
  render();
}

function templateCard(icon, title, text, color, action, tag='') {
  const bg = { green:'#cdeee7', pink:'#ffd5eb', purple:'#ded8ff', orange:'#ffd8b7', blue:'#dce8ff', gray:'#f5f5f6' }[color] || '#f5f5f6';
  return `<div class="template-card" onclick="${action}">${tag ? `<span class="badge business">${tag}</span>` : ''}<div class="template-icon" style="background:${bg}">${icon}</div><h3>${title}</h3><p>${text}</p></div>`;
}

function renderAIMain() {
  return `<div class="content wide">
    <div style="position:absolute;right:24px;top:68px;color:var(--muted)">▤ Memory</div>
    <div class="ai-hero">
      <div class="ai-logo">${flower()} <span>WorkMind<sup>2</sup></span></div>
      <div class="ai-box-wrap">
        <div class="ai-tabs"><button class="active">✽ Ask</button><button>👓 Agents</button></div>
        <div class="ai-input"><textarea id="aiPrompt" placeholder="Get instant answers, insights, and ideas."></textarea><div class="ai-input-foot"><div><button class="icon-btn flat">＋</button><button class="icon-btn flat">▤</button></div><div><button class="btn-ghost btn-small">✽ Max ▾</button><button class="icon-btn flat">🎙</button><button class="btn-primary btn-small" onclick="runAI()">Ask</button></div></div></div>
      </div>
      <div class="prompt-cards">
        ${aiPromptCard('▤','Project Summary','Summarize Project 1 status','Project Summary')}
        ${aiPromptCard('⌘','New Tasks','Create task action plan','New Tasks')}
        ${aiPromptCard('⚙','Status Report','Draft daily progress report','Status Report')}
        ${aiPromptCard('⌕','Locate Tasks','Find all pending tasks','Locate Tasks')}
      </div>
      <div id="aiResponse" class="ai-response"></div>
    </div>
    ${state.helper ? renderFeedbackWidget() : ''}
  </div>`;
}
function flower() { return `<div class="flower"><span></span><span></span><span></span><span></span><span></span><span></span></div>`; }
function aiPromptCard(icon,title,text,prompt) { return `<div class="prompt-card" onclick="runAISuggest('${prompt}')"><div>${icon}</div><h4>${title}</h4><p>${text}</p></div>`; }
function runAISuggest(prompt) { state.module='ai'; render(); setTimeout(() => { const box=$('#aiPrompt'); if(box){ box.value = prompt; runAI(); } }, 0); }
function runAI() {
  const prompt = ($('#aiPrompt')?.value || '').trim() || 'Project Summary';
  const response = aiResponseFor(prompt);
  const el = $('#aiResponse');
  if (!el) return;
  el.innerHTML = response;
  el.classList.add('show');
}
function aiResponseFor(prompt) {
  const open = state.tasks.filter(t=>t.projectId==='p1' && t.status!=='DONE');
  const blocked = open.filter(t=>t.status==='BLOCKED');
  const dueSoon = open.filter(t=>new Date(t.due) <= new Date('2026-07-09'));
  if (/new tasks|action/i.test(prompt)) {
    return `<h3>Task action plan</h3><p>I recommend creating 4 tasks: finalize dashboard card schema, unblock form field mapping, validate Gantt dependency behavior, and prepare demo script.</p><button class="btn-primary" onclick="createAITasks()">Create these tasks</button><div>${sourcePills(['Campaign dashboard wireframe','Project intake form automation','Task 2'])}</div>`;
  }
  if (/status/i.test(prompt)) {
    return `<h3>Daily status report</h3><p><b>BLUF:</b> Project 1 is moving, but one critical item is blocked. ${open.length} open tasks remain, ${blocked.length} blocked, and ${dueSoon.length} due soon. Recommend escalating intake automation and protecting time for dashboard delivery.</p><div>${sourcePills(open.map(t=>t.name).slice(0,4))}</div><br/><button class="btn-secondary" onclick="setModule('dashboards')">Open dashboard</button>`;
  }
  if (/locate|pending/i.test(prompt)) {
    return `<h3>Pending tasks located</h3>${renderInlineTaskActionTable(open)}<div>${sourcePills(open.map(t=>t.name))}</div>`;
  }
  if (/agent/i.test(prompt)) {
    return `<h3>Create Super Agent</h3><p>Recommended first agent: <b>Project Manager Agent</b>. It monitors status changes, blockers, stale tasks, and due-date risk. It can draft updates and request approvals before making changes.</p><button class="btn-primary" onclick="toast('Project Manager Agent created')">Create Project Manager Agent</button>`;
  }
  return `<h3>Project Summary</h3><p><b>Project 1 health:</b> ${blocked.length ? 'At Risk' : 'On Track'}. ${open.length} open tasks remain. The most important risk is ${blocked[0]?.name || 'none detected'}. Billable tracking is active and dashboard/reporting work is underway.</p><ul><li>Next best action: unblock form mapping.</li><li>AI schedule recommendation: protect a 90-minute focus block today.</li><li>Dashboard recommendation: add a blocker aging card.</li></ul><div>${sourcePills(['Project 1','Dashboard tasks','Form automation','Task activity'])}</div>`;
}
function sourcePills(items) { return items.map(i => `<span class="source-pill">Source: ${escapeHtml(i)}</span>`).join(''); }
function createAITasks() {
  ['Finalize dashboard card schema','Unblock form field mapping','Validate Gantt dependency behavior','Prepare demo script'].forEach((name, i) => {
    state.tasks.push({ id: uid(), projectId:'p1', name, assignee:i%2?'mira':'adrian', due:'2026-07-14', priority:i===1?'High':'Normal', status:'TO DO', comments:[{by:'WorkMind AI', text:'Created from AI task action plan.'}], estimate:2+i, tracked:0, billable:false, tags:['AI Plan'], progress:0, description:'AI-generated task.', start:'2026-07-10', duration:2, critical:i===1 });
  });
  toast('AI tasks created');
  state.module='spaces'; state.view='list'; render();
}

function renderPlannerMain() {
  const tasks = state.tasks.filter(t=>t.status!=='DONE').sort((a,b)=>priorityRank(a.priority)-priorityRank(b.priority));
  return `<div class="content">
    <div class="section-title"><div><h2>AI Planner</h2><p style="margin:4px 0 0;color:var(--muted)">Tasks and meetings converge into a priority-based daily schedule.</p></div><button class="btn-primary" onclick="toast('AI rescheduled your top priorities')">✽ Plan my day</button></div>
    <div class="planner-grid">
      <div class="report-card"><h3>Priority Queue</h3><div class="priority-list">${tasks.slice(0,7).map(t => `<div class="task-card" onclick="openTask('${t.id}')"><div class="task-card-title">${escapeHtml(t.name)}</div><div class="task-meta"><span>${t.priority}</span><span>${dateShort(t.due)}</span><span>${memberById(t.assignee).name}</span></div></div>`).join('')}</div></div>
      <div class="report-card"><h3>Today</h3>
        ${['08:30','09:30','11:00','13:00','14:30','16:00'].map((time,i) => `<div class="time-block"><div class="time">${time}</div><div class="timeline-panel"><b>${i===0?'Daily planning & inbox':tasks[i-1]?.name || 'Focus block'}</b><br/><span style="color:var(--muted)">${i===0?'AI review of blockers and due dates':'Scheduled from task priority, due date, and estimate'}</span></div><button class="btn-secondary btn-small" onclick="toast('Block updated')">Update</button></div>`).join('')}
      </div>
    </div>
  </div>`;
}
function priorityRank(p) { return {Urgent:0, High:1, Normal:2, Low:3}[p] ?? 4; }

function renderTeamsMain() {
  return `<div class="content"><div class="section-title"><div><h2>Teams Hub</h2><p style="margin:4px 0 0;color:var(--muted)">Team priorities, activity, capacity, and AI standups.</p></div><button class="btn-primary" onclick="toast('AI standup generated')">✽ Generate Standup</button></div>
  <div class="cards-grid">${state.members.map(m => {
    const owned = state.tasks.filter(t=>t.assignee===m.id);
    return `<div class="kpi-card"><div style="display:flex;gap:10px;align-items:center"><span class="avatar ${m.avatar}">${m.initials}</span><div><b>${m.name}</b><div style="color:var(--muted);font-size:12px">${m.role}</div></div></div><div class="value">${owned.length}</div><div class="trend">${owned.filter(t=>t.status==='BLOCKED').length} blockers • ${owned.reduce((s,t)=>s+t.estimate,0)}h estimate</div></div>`;
  }).join('')}</div><div class="section-title"><h2>Workload</h2></div><div class="report-card">${state.members.map(m => { const load=state.tasks.filter(t=>t.assignee===m.id && t.status!=='DONE').reduce((s,t)=>s+t.estimate,0); return `<div style="margin:12px 0"><div style="display:flex;justify-content:space-between"><b>${m.name}</b><span>${load}h planned</span></div><div class="progress ${load>8?'warn':'green'}"><span style="width:${Math.min(100,load*8)}%"></span></div></div>`}).join('')}</div></div>`;
}

function renderDocsMain() {
  ensureDocsState();
  const doc = selectedDoc();
  const stats = state.knowledgeStats || computeKnowledgeStatsLocal();
  const query = (state.knowledgeQuery || '').toLowerCase();
  const docs = state.docs.filter(d => !query || [d.title,d.kind,d.owner,d.content].join(' ').toLowerCase().includes(query));
  return `<div class="content wide"><div class="section-title"><div><h2>Docs, Wikis, Notes, and Decisions</h2><p style="margin:4px 0 0;color:var(--muted)">Shared knowledge connected to tasks, dashboards, goals, and AI.</p></div><div class="project-actions"><button class="btn-secondary" onclick="refreshDocsFromApi()">⟳ Refresh</button><button class="btn-secondary" onclick="createDecisionDemo()">＋ Decision</button><button class="btn-primary" onclick="createDocFromTemplate()">＋ New Doc</button></div></div>
    <div class="cards-grid compact">
      <div class="kpi-card"><span class="badge green">v0.8</span><h3>Knowledge docs</h3><div class="value">${stats.docs}</div><div class="trend">Docs, wikis, notes, and project plans</div></div>
      <div class="kpi-card"><span class="badge purple">Pages</span><h3>Wiki pages</h3><div class="value">${stats.pages}</div><div class="trend">${stats.verifiedPages || 0} verified/protected pages</div></div>
      <div class="kpi-card"><span class="badge blue">Traceability</span><h3>Linked tasks</h3><div class="value">${stats.linkedTasks}</div><div class="trend">Knowledge tied to execution</div></div>
      <div class="kpi-card"><span class="badge warn">Decisions</span><h3>Decision records</h3><div class="value">${stats.decisions}</div><div class="trend">Structured choices with rationale</div></div>
    </div>
    <div class="doc-workbench">
      <div class="doc-list-panel">
        <label class="search-lite"><span>⌕</span><input value="${escapeHtml(state.knowledgeQuery || '')}" placeholder="Search docs, decisions, SOPs..." oninput="setKnowledgeQuery(this.value)" /></label>
        <div class="doc-list">${docs.map(d => renderDocListItem(d)).join('') || `<div class="empty-small">No docs matched that search.</div>`}</div>
      </div>
      <div class="doc-editor-panel">
        ${doc ? renderDocEditor(doc) : `<div class="empty-center"><div class="big-icon">▤</div><h2>Select or create a doc</h2><p>Docs, wiki pages, and decisions stay linked to project work.</p></div>`}
      </div>
      <div class="doc-insights-panel">
        ${doc ? renderDocInsights(doc) : ''}
      </div>
    </div>
  </div>`;
}

function ensureDocsState(){
  state.docs = state.docs || [];
  if(!state.selectedDoc && state.docs[0]) state.selectedDoc = state.docs[0].id;
  state.knowledgeStats = state.knowledgeStats || computeKnowledgeStatsLocal();
}
function selectedDoc(){ ensureDocsState(); return state.docs.find(d=>d.id===state.selectedDoc) || state.docs[0]; }
function computeKnowledgeStatsLocal(){
  const docs = state.docs || [];
  return { docs: docs.length, pages: docs.reduce((s,d)=>s+(d.pages?.length || 1),0), linkedTasks: docs.reduce((s,d)=>s+(d.linkedTasks || d.linkCount || 0),0), decisions: docs.reduce((s,d)=>s+(d.decisionCount || d.decisions?.length || 0),0), verifiedPages: docs.reduce((s,d)=>s+(d.pages||[]).filter(p=>p.verified).length,0) };
}
function renderDocListItem(d){
  return `<button class="doc-list-item ${state.selectedDoc===d.id?'active':''}" onclick="openDoc('${d.id}')"><span class="badge ${d.kind==='Wiki'?'green':d.kind==='Decisions'?'warn':'blue'}">${escapeHtml(d.kind)}</span><b>${escapeHtml(d.title)}</b><span>${escapeHtml(d.owner)} • ${d.linkedTasks || d.linkCount || 0} linked tasks • ${d.decisionCount || d.decisions?.length || 0} decisions</span></button>`;
}
function renderDocEditor(doc){
  const pages = doc.pages || [{title:doc.title, content:doc.content || ''}];
  const content = doc.content || pages[0]?.content || '';
  return `<div class="doc-editor-head"><div><span class="badge ${doc.kind==='Wiki'?'green':doc.kind==='Decisions'?'warn':'blue'}">${escapeHtml(doc.kind)}</span><h2>${escapeHtml(doc.title)}</h2><p>Owner: ${escapeHtml(doc.owner)} • Updated ${escapeHtml(doc.updated || 'Today')}</p></div><div class="project-actions"><button class="btn-secondary" onclick="linkDocToTopTask()">Link top task</button><button class="btn-secondary" onclick="saveSelectedDoc()">Save</button><button class="btn-primary" onclick="summarizeSelectedDoc()">✽ AI Summary</button></div></div>
    <div class="doc-page-tabs">${pages.map((p,i)=>`<span class="doc-page-tab ${i===0?'active':''}">${p.verified?'✓ ':''}${escapeHtml(p.title || doc.title)}</span>`).join('')}<span class="doc-page-tab muted">＋ Page</span></div>
    <textarea id="docContent" class="doc-editor" oninput="draftDocContent(this.value)">${escapeHtml(content)}</textarea>`;
}
function renderDocInsights(doc){
  const linked = doc.linkedTaskRecords || linkRecordsForDocLocal(doc);
  const summary = doc.aiSummary || makeDocSummaryLocal(doc);
  const decisions = doc.decisions || [];
  return `<div class="insight-card ai"><h3>✽ AI document brief</h3><p>${escapeHtml(summary.summary || 'This document captures shared project knowledge.')}</p><div class="mini-list">${(summary.actionItems || ['Link this doc to active work']).map(i=>`<div>• ${escapeHtml(i)}</div>`).join('')}</div><button class="btn-primary btn-small" onclick="summarizeSelectedDoc()">Refresh AI brief</button></div>
    <div class="insight-card"><h3>Linked tasks</h3>${linked.slice(0,5).map(l=>`<div class="linked-row"><b>${escapeHtml(l.taskName || l.name)}</b><span>${escapeHtml(l.status || '')}</span></div>`).join('') || '<p class="muted">No tasks linked yet.</p>'}<button class="btn-secondary btn-small" onclick="linkDocToTopTask()">Link recommended task</button></div>
    <div class="insight-card"><h3>Decisions</h3>${decisions.slice(0,4).map(d=>`<div class="decision-row"><b>${escapeHtml(d.title)}</b><span>${escapeHtml(d.status || 'Accepted')}</span></div>`).join('') || '<p class="muted">No structured decisions yet.</p>'}<button class="btn-secondary btn-small" onclick="createDecisionDemo()">Capture decision</button></div>
    <div class="insight-card"><h3>Version history</h3>${(doc.versions || [{versionNumber:1,createdAt:'local'}]).slice(0,4).map(v=>`<div class="linked-row"><span>v${v.versionNumber || 1}</span><span>${dateShort(v.createdAt || 'Today')}</span></div>`).join('')}</div>`;
}
function setKnowledgeQuery(value){ state.knowledgeQuery = value; render(); }
function openDoc(id){ state.selectedDoc = id; render(); if(apiOnline) fetchDocDetail(id); }
function draftDocContent(value){ const doc=selectedDoc(); if(doc){ doc.content=value; doc.updated='Draft'; saveState(); } }
function linkRecordsForDocLocal(doc){
  const names = (doc.content || '').toLowerCase();
  return state.tasks.filter(t => (t.tags||[]).some(tag=>names.includes(String(tag).toLowerCase())) || names.includes(t.name.toLowerCase().split(' ')[0])).slice(0,4).map(t=>({taskId:t.id,taskName:t.name,status:t.status,assignee:t.assignee,due:t.due,relation:'inferred'}));
}
function makeDocSummaryLocal(doc){
  const linked = linkRecordsForDocLocal(doc);
  const content = (doc.content || '').replace(/[#*-]/g,' ').replace(/\s+/g,' ').trim();
  return { summary: content.slice(0,220) || `${doc.title} is ready for project notes, decisions, and linked task context.`, linkedTaskCount: linked.length, decisionCount: doc.decisionCount || 0, risk: linked.some(l=>l.status==='BLOCKED')?'medium':'low', actionItems: linked.some(l=>l.status==='BLOCKED') ? ['Resolve linked blocked task before next status update'] : ['Add at least one linked task or decision before publishing'] };
}
async function fetchDocDetail(id){
  try{ const res=await fetch(`${API_BASE}/docs/${id}`, {headers:authHeaders(), cache:'no-store'}); if(res.ok){ const data=await res.json(); if(data.doc){ upsertDocLocal(data.doc); saveState(); render(); } } }catch(e){ console.warn(e); }
}
function upsertDocLocal(doc){ const idx=state.docs.findIndex(d=>d.id===doc.id); if(idx>=0) state.docs[idx]=doc; else state.docs.unshift(doc); state.knowledgeStats=computeKnowledgeStatsLocal(); }
async function refreshDocsFromApi(){
  ensureDocsState();
  if(!apiOnline){ toast('Knowledge hub running locally'); render(); return; }
  try{ const res=await fetch(`${API_BASE}/docs`, {headers:authHeaders(), cache:'no-store'}); if(!res.ok) throw new Error('Docs API failed'); const data=await res.json(); state.docs=data.docs || state.docs; state.knowledgeStats=data.stats || computeKnowledgeStatsLocal(); if(!state.selectedDoc && state.docs[0]) state.selectedDoc=state.docs[0].id; toast('Docs refreshed from API'); saveState(); render(); }catch(e){ console.warn(e); toast('Docs API unavailable; using local knowledge'); }
}
async function saveSelectedDoc(){
  const doc=selectedDoc(); if(!doc) return; const content=$('#docContent')?.value || doc.content || ''; doc.content=content; doc.updated='Today';
  if(apiOnline){ try{ const res=await fetch(`${API_BASE}/docs/${doc.id}`, {method:'PATCH', headers:{'Content-Type':'application/json', ...authHeaders()}, body:JSON.stringify({title:doc.title, kind:doc.kind, content})}); if(res.ok){ const data=await res.json(); if(data.doc) upsertDocLocal(data.doc); toast('Doc saved to API'); saveState(); render(); return; }}catch(e){ console.warn(e); }}
  toast('Doc saved locally'); saveState(); render();
}
async function createDocFromTemplate(){
  const payload={title:'New Project Notes', kind:'Doc', owner:'Adrian Francis', content:'# New Project Notes\n\n## Context\n\n## Decisions\n\n## Action Items\n- '};
  if(apiOnline){ try{ const res=await fetch(`${API_BASE}/docs`, {method:'POST', headers:{'Content-Type':'application/json', ...authHeaders()}, body:JSON.stringify(payload)}); if(res.ok){ const data=await res.json(); upsertDocLocal(data.doc); state.selectedDoc=data.doc.id; toast('Doc created'); saveState(); render(); return; }}catch(e){ console.warn(e); }}
  const doc={id:uid(), ...payload, updated:'Today', linkedTasks:0, decisionCount:0, pages:[{id:uid(),title:payload.title,content:payload.content,verified:false,protected:false}], versions:[{versionNumber:1,createdAt:new Date().toISOString()}]}; state.docs.unshift(doc); state.selectedDoc=doc.id; state.knowledgeStats=computeKnowledgeStatsLocal(); toast('Doc created locally'); saveState(); render();
}
async function summarizeSelectedDoc(){
  const doc=selectedDoc(); if(!doc) return;
  if(apiOnline){ try{ const res=await fetch(`${API_BASE}/docs/${doc.id}/ai-summary`, {method:'POST', headers:authHeaders()}); if(res.ok){ const data=await res.json(); if(data.doc) upsertDocLocal(data.doc); const msg=data.summary?.summary || 'AI summary generated'; toast('AI summary generated'); showModal('AI Document Summary', `<p>${escapeHtml(msg)}</p><ul>${(data.summary?.actionItems||[]).map(i=>`<li>${escapeHtml(i)}</li>`).join('')}</ul>`); render(); return; }}catch(e){ console.warn(e); }}
  doc.aiSummary=makeDocSummaryLocal(doc); showModal('AI Document Summary', `<p>${escapeHtml(doc.aiSummary.summary)}</p><ul>${doc.aiSummary.actionItems.map(i=>`<li>${escapeHtml(i)}</li>`).join('')}</ul>`); toast('AI summary generated locally'); render();
}
async function linkDocToTopTask(){
  const doc=selectedDoc(); const task=state.tasks.find(t=>t.status==='BLOCKED') || state.tasks.find(t=>t.status!=='DONE'); if(!doc||!task) return;
  if(apiOnline){ try{ const res=await fetch(`${API_BASE}/docs/${doc.id}/links`, {method:'POST', headers:{'Content-Type':'application/json', ...authHeaders()}, body:JSON.stringify({task_id:task.id, relation:'references'})}); if(res.ok){ const data=await res.json(); if(data.doc) upsertDocLocal(data.doc); toast('Doc linked to task'); saveState(); render(); return; }}catch(e){ console.warn(e); }}
  doc.linkedTaskRecords=doc.linkedTaskRecords||[]; if(!doc.linkedTaskRecords.some(l=>l.taskId===task.id)) doc.linkedTaskRecords.push({taskId:task.id,taskName:task.name,status:task.status,assignee:task.assignee,due:task.due,relation:'references'}); doc.linkedTasks=(doc.linkedTasks||0)+1; state.knowledgeStats=computeKnowledgeStatsLocal(); toast('Doc linked locally'); saveState(); render();
}
async function createDecisionDemo(){
  const doc=selectedDoc() || state.docs.find(d=>d.kind==='Decisions'); if(!doc) return; const payload={title:'Confirm v0.8 knowledge workflow', decision:'Use Docs, wiki pages, decisions, and task links as the knowledge backbone for project execution.', rationale:'This makes AI summaries traceable and keeps project context tied to live work.', owner:'Adrian Francis', status:'Accepted'};
  if(apiOnline){ try{ const res=await fetch(`${API_BASE}/docs/${doc.id}/decisions`, {method:'POST', headers:{'Content-Type':'application/json', ...authHeaders()}, body:JSON.stringify(payload)}); if(res.ok){ const data=await res.json(); if(data.doc) upsertDocLocal(data.doc); toast('Decision captured'); saveState(); render(); return; }}catch(e){ console.warn(e); }}
  doc.decisions=doc.decisions||[]; doc.decisions.unshift({...payload,id:uid(),createdAt:new Date().toISOString()}); doc.decisionCount=(doc.decisionCount||0)+1; state.knowledgeStats=computeKnowledgeStatsLocal(); toast('Decision captured locally'); saveState(); render();
}
function showModal(title, body){
  let el=$('.modal-pop'); if(!el){ el=document.createElement('div'); el.className='modal-pop'; document.body.appendChild(el); }
  el.innerHTML=`<div class="modal-card"><button class="modal-close" onclick="this.closest('.modal-pop').remove()">×</button><h2>${escapeHtml(title)}</h2>${body}</div>`;
}

function renderWhiteboardsMain() {
  return `<div class="content"><div class="section-title"><div><h2>Visual Collaboration</h2><p style="margin:4px 0 0;color:var(--muted)">Whiteboards, canvas planning, and mind maps that convert ideas into coordinated action.</p></div><button class="btn-primary" onclick="toast('Sticky note converted to task')">Convert note to task</button></div>
    <div class="whiteboard-canvas">
      <div class="sticky yellow">Project idea<br/><br/>AI turns this into a project plan.</div>
      <div class="sticky blue">Dashboard card<br/><br/>Live KPI with task drill-down.</div>
      <div class="sticky pink">Form intake<br/><br/>Centralize requests and trigger workflows.</div>
      <div class="sticky green">Automation<br/><br/>Escalate blocked work automatically.</div>
      <div class="connector-line" style="left:230px;top:142px;width:120px;transform:rotate(25deg)"></div>
      <div class="connector-line" style="left:470px;top:180px;width:120px;transform:rotate(-30deg)"></div>
      <div class="connector-line" style="left:670px;top:180px;width:120px;transform:rotate(35deg)"></div>
    </div>
  </div>`;
}

function renderGoalsMain() {
  return `<div class="content"><div class="section-title"><div><h2>Goals and OKRs</h2><p style="margin:4px 0 0;color:var(--muted)">Company goals linked directly to tasks, dashboards, and rollups.</p></div><button class="btn-primary" onclick="toast('New goal placeholder')">＋ Goal</button></div>
    <div class="goal-grid">${state.goals.map(g => `<div class="goal-card"><span class="badge ${g.status==='At Risk'?'warn':'green'}">${g.status}</span><h3>${escapeHtml(g.name)}</h3><p>Owner: ${g.owner}</p><div class="progress ${g.status==='At Risk'?'warn':'green'}"><span style="width:${g.progress}%"></span></div><br/><button class="btn-secondary" onclick="toast('Goal drill-down opened')">Drill down</button></div>`).join('')}</div>
  </div>`;
}

function renderClipsMain() {
  return `<div class="content"><div class="empty-center"><div class="big-icon">▰</div><h2>Record clips where work happens</h2><div>Screen recordings, voice notes, transcripts, and bug reports will attach directly to tasks and docs.</div><br/><button class="btn-primary" onclick="toast('Clip recording placeholder')">Record Clip</button></div></div>`;
}

function showDataLayerStatus() {
  const message = apiOnline
    ? `Connected to the v0.5 reporting API. ${authStatusText}. Last sync: ${lastSyncAt ? lastSyncAt.toLocaleTimeString() : 'just now'}.`
    : 'Running in local fallback mode. Start Docker Compose to enable FastAPI persistence.';
  toast(message);
}

function renderDataLayerCards() {
  const tasks = state.tasks.length;
  const projects = state.spaces.flatMap(s => s.folders || []).flatMap(f => f.lists || []).filter(l => l.kind === 'project').length;
  const comments = state.tasks.reduce((sum, t) => sum + (t.comments?.length || 0), 0);
  return `<div class="cards-grid">
    <div class="kpi-card"><span class="badge ${apiOnline ? 'green' : 'warn'}">${apiOnline ? 'Online' : 'Offline fallback'}</span><h3>v0.5 Reporting + Data</h3><div class="value">${apiOnline ? 'API' : 'Local'}</div><div class="trend">${apiStatusText}</div><button class="btn-secondary" onclick="showDataLayerStatus()">Check status</button></div>
    <div class="kpi-card"><h3>Persisted tasks</h3><div class="value">${tasks}</div><div class="trend">${projects} projects • ${comments} comments • report actions enabled</div><button class="btn-secondary" onclick="syncStateToApi(); toast('Manual sync requested')">Sync now</button></div>
    <div class="kpi-card"><span class="badge green">Auth</span><h3>Demo sign-in</h3><div class="value">${currentUser ? 'Active' : 'Local'}</div><div class="trend">${authStatusText}<br/>Demo email: echofoxx@gmail.com</div><button class="btn-secondary" onclick="ensureDemoAuth(); toast('Demo authentication requested')">Sign in</button></div>
    <div class="kpi-card"><span class="badge green">New</span><h3>API endpoints</h3><p class="trend">/api/reports/dashboard, /api/reports/drilldown, /api/reports/actions, /api/reports/cards</p><button class="btn-secondary" onclick="window.open('/api/docs','_blank')">Open API docs</button></div>
  </div>`;
}

function renderMoreMain() {
  return `<div class="content"><div class="section-title"><div><h2>Automations and Connected Tools</h2><p style="margin:4px 0 0;color:var(--muted)">Streamline projects, scheduling, engineering, agencies, customer management, and persistent API-backed work data.</p></div><button class="btn-primary" onclick="toast('Create automation')">＋ Automation</button></div>
    ${renderDataLayerCards()}
    <div class="section-title"><h2>Automation templates</h2></div>
    <div class="auto-grid">${state.automations.map(a => `<div class="auto-card"><span class="badge ${a.enabled?'green':''}">${a.enabled?'Enabled':'Paused'}</span><h3>${escapeHtml(a.name)}</h3><p>${a.category}<br/><b>When:</b> ${a.trigger}<br/><b>Then:</b> ${a.action}</p><button class="btn-secondary" onclick="toggleAutomation('${a.id}')">${a.enabled?'Pause':'Enable'}</button></div>`).join('')}
    ${['Auto-assign urgent tasks','Notify when due date missed','Create kickoff checklist','Generate weekly status report','Move task when checklist complete','Create bug from failed build','Create client follow-up','Escalate stale approvals'].map(name => `<div class="auto-card"><span class="badge">Template</span><h3>${name}</h3><p>Trigger, condition, and action template ready to customize.</p><button class="btn-primary" onclick="toast('Automation template added')">Use template</button></div>`).join('')}
    </div>
  </div>`;
}
function toggleAutomation(id){ const a=state.automations.find(x=>x.id===id); a.enabled=!a.enabled; toast(a.enabled?'Automation enabled':'Automation paused'); render(); }

function renderInviteMain() {
  return `<div class="content"><div class="empty-center"><div class="big-icon">♙+</div><h2>Invite your team</h2><div>Add teammates, guests, agencies, clients, or stakeholders to collaborate in controlled workspaces.</div><br/><button class="btn-primary" onclick="toast('Invite sent placeholder')">Invite people</button></div></div>`;
}
function renderUpgradeMain() {
  return `<div class="content"><div class="template-wrap"><h1>Upgrade your WorkOS</h1><p>Unlock Super Agents, unlimited dashboards, advanced automations, guests, audit logs, and enterprise controls.</p><div class="template-grid">${templateCard('✽','AI Plus','More AI usage, agents, and premium models','purple', 'toast("Upgrade placeholder")')}${templateCard('⚡','Automation Pro','Advanced rules and connected workflows','orange','toast("Upgrade placeholder")')}${templateCard('🔐','Enterprise','SSO, audit logs, roles, governance','blue','toast("Upgrade placeholder")')}</div></div></div>`;
}

function renderFeedbackWidget() {
  return `<div class="helper-card"><button class="helper-close" onclick="state.helper=false; render()">×</button><div class="helper-body"><div>Is Thing Planner working <b>as expected</b> today?</div><div class="thumbs"><button onclick="toast('Thanks for the feedback')">👎</button><button onclick="toast('Thanks for the feedback')">👍</button></div></div></div>`;
}
function renderBrainPromoWidget() {
  return `<div class="helper-card compact"><button class="helper-close" onclick="state.aiPromo=false; render()">×</button><div class="brain-promo-img"><div class="brain-mini-panel"><b>✽ WorkMind</b><br/><br/>• 9 Tasks completed<br/>• Approved Q3 budget<br/><br/><b>⚠ Needs you before EOD</b><br/>• Approve Invoices<br/>• Reply to Dave's email</div></div><div class="brain-promo-foot"><b>Let WorkMind help you wrap up your week</b><p>WorkMind already knows what you worked on. One click and you're weekend-ready.</p><button class="btn-primary" onclick="setModule('ai')">Wrap up my week</button></div></div>`;
}

function bindEvents() {
  // placeholder for future keyboard shortcuts and focus handling
}

function globalSearch(query) {
  const q = (query || '').trim().toLowerCase();
  if (!q) return;
  const found = state.tasks.find(t => t.name.toLowerCase().includes(q) || t.tags.join(' ').toLowerCase().includes(q));
  if (found) { state.module='spaces'; state.selectedProject=found.projectId; selectedTaskId=found.id; render(); }
  else toast('No matching task in demo data');
}

function memberById(id) { return state.members.find(m => m.id === id) || state.members[0]; }
function dateShort(d) { try { return new Date(d + 'T00:00:00').toLocaleDateString(undefined, { month:'short', day:'numeric' }); } catch { return d; } }
function uid() { return Math.random().toString(36).slice(2, 9); }
function escapeHtml(str) { return String(str ?? '').replace(/[&<>'"]/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[s])); }

// v0.5 Forms + Intake Automation Engine overrides
function formAnalyticsLocal() {
  const submissions = state.formSubmissions || [];
  const byDepartment = {};
  const byPriority = {};
  let duplicateWatch = 0;
  submissions.forEach(s => {
    byDepartment[s.department || 'Unknown'] = (byDepartment[s.department || 'Unknown'] || 0) + 1;
    byPriority[s.priority || 'Normal'] = (byPriority[s.priority || 'Normal'] || 0) + 1;
    if (['medium','high'].includes(s.aiAnalysis?.duplicate_risk)) duplicateWatch++;
  });
  return { total: submissions.length, byDepartment, byPriority, duplicateWatch };
}

function renderFormsMain() {
  if (formBuilderOpen) return renderFormBuilder();
  const analytics = formAnalyticsLocal();
  const latest = (state.formSubmissions || []).slice(0, 5);
  return `<div class="content wide">
    <div class="section-title"><div><h2>Forms and Intake Automation</h2><p style="margin:4px 0 0;color:var(--muted)">v0.5 connected forms create work, trigger AI analysis, route requests, and write automation run history.</p></div><div><button class="btn-secondary" onclick="refreshFormsFromApi()">⟳ Refresh</button><button class="btn-primary" onclick="openFormBuilder()">＋ Build Form</button></div></div>
    <div class="cards-grid">
      <div class="kpi-card"><span class="badge green">Connected</span><h3>Processed submissions</h3><div class="value">${analytics.total}</div><div class="trend">${state.forms.reduce((s,f)=>s+(f.submissions||0),0)} lifetime submissions across ${state.forms.length} forms</div></div>
      <div class="kpi-card"><span class="badge purple">AI</span><h3>AI intake analysis</h3><div class="value">${analytics.duplicateWatch}</div><div class="trend">duplicate / related-work reviews suggested</div><button class="btn-secondary" onclick="toast('AI reviewed form submissions and refreshed intake insights')">Analyze</button></div>
      <div class="kpi-card"><span class="badge green">Automation</span><h3>Automation runs</h3><div class="value">${(state.automationRuns||[]).length}</div><div class="trend">classification • task creation • notification • dashboard refresh</div><button class="btn-secondary" onclick="runManualAutomation()">Run test</button></div>
      <div class="kpi-card"><span class="badge ${apiOnline?'green':'warn'}">${apiOnline?'API':'Local'}</span><h3>Intake API</h3><p class="trend">/api/forms, /api/forms/{id}/submissions, /api/forms/{id}/analytics, /api/automations/run</p><button class="btn-secondary" onclick="window.open('/api/docs','_blank')">Open API docs</button></div>
    </div>
    <div class="section-title"><h2>Choose a Form template</h2><button class="btn-secondary" onclick="openFormBuilder()">Start from scratch</button></div>
    <div class="template-grid">
      ${templateCard('🎛','Feedback Form','Survey and collect feedback with AI sentiment','green', 'openFormBuilder()')}
      ${templateCard('📋','Project Intake','Create kickoff tasks, route owners, and analyze objectives','pink', 'openFormBuilder()')}
      ${templateCard('🧺','Order Form','Capture and process client orders','purple', 'openFormBuilder()')}
      ${templateCard('👤','Job Application','Accept and triage applications','orange', 'openFormBuilder()')}
      ${templateCard('🧾','IT Requests','Route service requests and severity','blue', 'openFormBuilder()')}
      ${templateCard('⚡','Automation-backed Form','Build form + trigger chain together','gray', 'openFormBuilder()')}
    </div>
    <div class="section-title"><h2>Latest submissions</h2><button class="btn-secondary" onclick="submitFormDemo()">Submit demo intake</button></div>
    <div class="report-card"><table class="report-table"><thead><tr><th>Request</th><th>Requester</th><th>Department</th><th>Priority</th><th>AI analysis</th><th>Task</th></tr></thead><tbody>
      ${latest.map(s => `<tr><td><b>${escapeHtml(s.payload?.project_name || s.payload?.request || 'Intake request')}</b><br/><span class="muted">${escapeHtml(s.status || 'Processed')}</span></td><td>${escapeHtml(s.requester || '')}</td><td>${escapeHtml(s.department || '')}</td><td><span class="badge ${s.priority==='Urgent'?'red':s.priority==='High'?'warn':'green'}">${escapeHtml(s.priority || 'Normal')}</span></td><td>${escapeHtml(s.aiAnalysis?.summary || s.aiAnalysis?.classification || 'AI classified and routed')}</td><td><button class="btn-secondary btn-small" onclick="openTask('${s.createdTaskId || ''}')">Open</button></td></tr>`).join('') || `<tr><td colspan="6">No submissions yet. Submit a demo intake to create the first task.</td></tr>`}
    </tbody></table></div>
    ${state.aiPromo ? renderBrainPromoWidget() : ''}
  </div>`;
}

function renderFormBuilder() {
  const fields = [
    ['project_name','Project name','short text','task.name'],
    ['requester','Requester','person/email','submission.requester'],
    ['department','Department','dropdown','task.tags + routing'],
    ['priority','Priority','dropdown','task.priority'],
    ['desired_due_date','Desired due date','date','task.due'],
    ['business_objective','Business objective','long text','task.description'],
    ['attachment','Attachment','file','task.attachment']
  ];
  return `<div class="content wide">
    <div class="section-title"><div><h2>Project Intake Form Builder</h2><p style="margin:4px 0 0;color:var(--muted)">Map fields to task properties, then chain AI classification, task creation, notification, and dashboard update automations.</p></div><div><button class="btn-secondary" onclick="formBuilderOpen=false;render()">Templates</button><button class="btn-secondary" onclick="saveFormSchemaDemo()">Save schema</button><button class="btn-primary" onclick="submitFormDemo()">Submit test response</button></div></div>
    <div class="form-builder v05-form-builder">
      <div class="report-card"><h3>Fields and mapping</h3>
        ${fields.map((f,i) => `<div class="mapping-row"><div><b>${i+1}. ${escapeHtml(f[1])}</b><br/><span>${escapeHtml(f[2])}</span></div><span class="badge">${escapeHtml(f[3])}</span></div>`).join('')}
        <div class="hr"></div><button class="btn-secondary" onclick="toast('Field added to builder')">＋ Add Field</button>
        <button class="btn-primary" style="margin-left:8px" onclick="toast('AI suggested conditional priority routing and duplicate detection')">✽ AI Improve</button>
      </div>
      <div class="form-preview">
        <h2>Project Intake</h2><p style="color:var(--muted)">Use this form to centralize new work, create a task, route the owner, and trigger intake automations.</p>
        <div class="form-field"><label>Project name *</label><input id="formProjectName" placeholder="e.g., Launch customer dashboard" /></div>
        <div class="form-field"><label>Requester *</label><input id="formRequester" placeholder="Name or email" value="Adrian Francis" /></div>
        <div class="form-field"><label>Department</label><select id="formDepartment"><option>Product</option><option>Engineering</option><option>Marketing</option><option>Operations</option><option>Finance</option></select></div>
        <div class="form-field"><label>Priority</label><select id="formPriority"><option>Normal</option><option>High</option><option>Urgent</option></select></div>
        <div class="form-field"><label>Desired due date</label><input id="formDue" type="date" value="2026-07-15" /></div>
        <div class="form-field"><label>Business objective</label><textarea id="formObjective" placeholder="What result should this project deliver?"></textarea></div>
        <button class="btn-primary" onclick="submitFormDemo()">Submit request</button>
      </div>
      <div class="report-card"><h3>Automation chain</h3>
        ${['AI classify request','Create mapped task','Add AI intake comment','Notify recommended owner','Refresh dashboard analytics'].map((step,i)=>`<div class="auto-step"><span>${i+1}</span><div><b>${step}</b><br/><em>${i<3?'Enabled now':'Ready for rule expansion'}</em></div></div>`).join('')}
      </div>
    </div>
  </div>`;
}

async function submitFormDemo() {
  const fields = {
    project_name: ($('#formProjectName')?.value || 'New intake request from Form').trim(),
    requester: ($('#formRequester')?.value || 'Adrian Francis').trim(),
    department: $('#formDepartment')?.value || 'Product',
    priority: $('#formPriority')?.value || 'Normal',
    desired_due_date: $('#formDue')?.value || '2026-07-15',
    business_objective: ($('#formObjective')?.value || 'Created from Project Intake Form.').trim()
  };
  if (apiOnline) {
    try {
      const res = await fetch(`${API_BASE}/forms/form1/submissions`, { method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() }, body: JSON.stringify({ form_id:'form1', fields }) });
      if (!res.ok) throw new Error('Form submission failed');
      const data = await res.json();
      if (data.state) state = { ...state, ...data.state };
      await refreshReportDataset(true);
      toast(`Form submitted → task created + ${data.automation_chain?.length || 0} automations ran`);
      formBuilderOpen = false; state.module = 'spaces'; state.selectedProject = data.task?.projectId || 'p1'; state.view = 'list'; saveState(); render();
      return;
    } catch (err) { console.warn('API form submission failed', err); toast('API unavailable; using local form submission'); }
  }
  const owner = fields.department === 'Engineering' ? 'tom' : 'mira';
  const task = { id: uid(), projectId: 'p1', name: `Intake: ${fields.project_name}`, assignee: owner, due: fields.desired_due_date, priority: fields.priority, status: 'TO DO', comments: [{ by:'AI Intake Agent', text:`AI classified this request as Project Intake and suggested ${memberById(owner).name} as owner.`}], estimate: fields.priority === 'Normal' ? 2 : 4, tracked: 0, billable: false, tags: ['Intake','AI',fields.department], progress: 0, description: fields.business_objective, start: fields.desired_due_date, duration: 3, critical: fields.priority !== 'Normal' };
  state.tasks.push(task);
  state.formSubmissions = state.formSubmissions || [];
  state.formSubmissions.unshift({ id:uid(), formId:'form1', requester:fields.requester, department:fields.department, priority:fields.priority, payload:fields, aiAnalysis:{classification:'Project Intake', risk:fields.priority==='Urgent'?'high':fields.priority==='High'?'medium':'low', recommended_owner:owner, duplicate_risk:'medium', summary:`AI classified '${fields.project_name}' and routed it to ${memberById(owner).name}.`}, createdTaskId:task.id, status:'Processed', createdAt:new Date().toISOString() });
  state.automationRuns = state.automationRuns || [];
  ['auto_intake_classify','auto_intake_task','auto_intake_notify'].forEach(id => state.automationRuns.unshift({ id:uid(), automationId:id, trigger:'Form submitted', sourceType:'form_submission', sourceId:state.formSubmissions[0].id, status:'success', summary:`${id.replaceAll('_',' ')} completed`, details:{task_id:task.id}, createdAt:new Date().toISOString() }));
  const form = state.forms.find(f=>f.id==='form1'); if (form) form.submissions = (form.submissions||0)+1;
  toast('Form submitted → task created + automations ran');
  formBuilderOpen = false; state.module = 'spaces'; state.selectedProject = 'p1'; state.view = 'list'; saveState(); render();
}

async function refreshFormsFromApi() {
  if (!apiOnline) { toast('Running local form analytics'); render(); return; }
  try {
    const [formsRes, subsRes, autosRes] = await Promise.all([
      fetch(`${API_BASE}/forms`, { headers: authHeaders(), cache:'no-store' }),
      fetch(`${API_BASE}/forms/form1/submissions`, { headers: authHeaders(), cache:'no-store' }),
      fetch(`${API_BASE}/automations`, { headers: authHeaders(), cache:'no-store' })
    ]);
    if (formsRes.ok) state.forms = (await formsRes.json()).forms || state.forms;
    if (subsRes.ok) state.formSubmissions = (await subsRes.json()).submissions || state.formSubmissions;
    if (autosRes.ok) { const data = await autosRes.json(); state.automations = data.automations || state.automations; state.automationRuns = data.runs || state.automationRuns; }
    toast('Forms, submissions, and automations refreshed'); saveState(); render();
  } catch (err) { console.warn(err); toast('Could not refresh forms from API'); }
}

async function saveFormSchemaDemo() {
  const schema = { mode:'task_intake', target_project_id:'p1', ai_analysis:true, fields:['project_name','requester','department','priority','desired_due_date','business_objective'], automation_chain:['auto_intake_classify','auto_intake_task','auto_intake_notify','auto_intake_dashboard'] };
  if (apiOnline) {
    try {
      const res = await fetch(`${API_BASE}/forms/form1/schema`, { method:'PUT', headers:{ 'Content-Type':'application/json', ...authHeaders() }, body: JSON.stringify({ name:'Project Intake', description:'Streamline new project requests with AI routing', schema }) });
      if (!res.ok) throw new Error('schema save failed');
      toast('Form schema saved to API'); return;
    } catch (err) { console.warn(err); }
  }
  const f = state.forms.find(x=>x.id==='form1'); if (f) f.schema = schema; toast('Form schema saved locally'); saveState();
}

async function runManualAutomation() {
  if (apiOnline) {
    try {
      const res = await fetch(`${API_BASE}/automations/run`, { method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders() }, body: JSON.stringify({ automation_id:'auto_intake_dashboard', trigger:'manual', source_type:'forms', source_id:'form1', details:{requested_from:'frontend'} }) });
      if (res.ok) { const data = await res.json(); if (data.state) state = { ...state, ...data.state }; toast('Manual automation run recorded'); saveState(); render(); return; }
    } catch (err) { console.warn(err); }
  }
  state.automationRuns = state.automationRuns || [];
  state.automationRuns.unshift({ id:uid(), automationId:'auto_intake_dashboard', trigger:'manual', sourceType:'forms', sourceId:'form1', status:'success', summary:'Manual automation run recorded locally', details:{}, createdAt:new Date().toISOString() });
  toast('Manual automation run recorded locally'); saveState(); render();
}

function renderMoreMain() {
  const runs = (state.automationRuns || []).slice(0, 6);
  return `<div class="content wide"><div class="section-title"><div><h2>Automations and Connected Tools</h2><p style="margin:4px 0 0;color:var(--muted)">v0.6 adds an AI planner and scheduling engine plus the v0.5 intake automation engine with run history, form triggers, and connected task creation.</p></div><button class="btn-primary" onclick="runManualAutomation()">▶ Run Test Automation</button></div>
    ${renderDataLayerCards()}
    <div class="section-title"><h2>Automation templates</h2><button class="btn-secondary" onclick="setModule('forms')">Open Forms</button></div>
    <div class="auto-grid">${state.automations.map(a => `<div class="auto-card"><span class="badge ${a.enabled?'green':''}">${a.enabled?'Enabled':'Paused'}</span><h3>${escapeHtml(a.name)}</h3><p>${escapeHtml(a.category)}<br/><b>When:</b> ${escapeHtml(a.trigger)}<br/><b>Then:</b> ${escapeHtml(a.action)}</p><button class="btn-secondary" onclick="toggleAutomation('${a.id}')">${a.enabled?'Pause':'Enable'}</button></div>`).join('')}
    ${['Escalate urgent intake','Route agency kickoff','Create approval request','Refresh form dashboard','Create follow-up from report','Notify client success'].map(name => `<div class="auto-card"><span class="badge">Template</span><h3>${name}</h3><p>Trigger, condition, and action template ready to customize.</p><button class="btn-primary" onclick="toast('Automation template added')">Use template</button></div>`).join('')}</div>
    <div class="section-title"><h2>Automation run history</h2><button class="btn-secondary" onclick="refreshFormsFromApi()">Refresh runs</button></div>
    <div class="report-card"><table class="report-table"><thead><tr><th>Run</th><th>Trigger</th><th>Source</th><th>Status</th><th>Time</th></tr></thead><tbody>${runs.map(r=>`<tr><td>${escapeHtml(r.summary)}</td><td>${escapeHtml(r.trigger)}</td><td>${escapeHtml(r.sourceType)} / ${escapeHtml(r.sourceId)}</td><td><span class="badge green">${escapeHtml(r.status)}</span></td><td>${new Date(r.createdAt).toLocaleString()}</td></tr>`).join('') || '<tr><td colspan="5">No automation runs yet.</td></tr>'}</tbody></table></div>
  </div>`;
}

async function toggleAutomation(id){
  if (apiOnline) {
    try {
      const res = await fetch(`${API_BASE}/automations/${id}/toggle`, { method:'PATCH', headers: authHeaders() });
      if (res.ok) { const data = await res.json(); if (data.state) state = { ...state, ...data.state }; toast(data.enabled?'Automation enabled':'Automation paused'); saveState(); render(); return; }
    } catch (err) { console.warn(err); }
  }
  const a=state.automations.find(x=>x.id===id); if (!a) return; a.enabled=!a.enabled; toast(a.enabled?'Automation enabled':'Automation paused'); saveState(); render();
}

function renderDataLayerCards() {
  const tasks = state.tasks.length;
  const projects = state.spaces.flatMap(s => s.folders || []).flatMap(f => f.lists || []).filter(l => l.kind === 'project').length;
  const comments = state.tasks.reduce((sum, t) => sum + (t.comments?.length || 0), 0);
  const submissions = (state.formSubmissions || []).length;
  const runs = (state.automationRuns || []).length;
  return `<div class="cards-grid">
    <div class="kpi-card"><span class="badge ${apiOnline ? 'green' : 'warn'}">${apiOnline ? 'Online' : 'Offline fallback'}</span><h3>v0.9 Visual Collaboration</h3><div class="value">${apiOnline ? 'API' : 'Local'}</div><div class="trend">${apiStatusText}</div><button class="btn-secondary" onclick="showDataLayerStatus()">Check status</button></div>
    <div class="kpi-card"><h3>Persisted tasks</h3><div class="value">${tasks}</div><div class="trend">${projects} projects • ${comments} comments • intake actions enabled</div><button class="btn-secondary" onclick="syncStateToApi(); toast('Manual sync requested')">Sync now</button></div>
    <div class="kpi-card"><span class="badge purple">Forms</span><h3>Submissions</h3><div class="value">${submissions}</div><div class="trend">AI analysis and task routing available</div><button class="btn-secondary" onclick="setModule('forms')">Open forms</button></div>
    <div class="kpi-card"><span class="badge green">Automation</span><h3>Run history</h3><div class="value">${runs}</div><div class="trend">/api/automations and /api/automations/run</div><button class="btn-secondary" onclick="window.open('/api/docs','_blank')">Open API docs</button></div>
  </div>`;
}



// v0.6 Planner + AI Scheduling Engine overrides
function plannerToday() { return new Date().toISOString().slice(0, 10); }
function ensurePlannerState() {
  state.version = '0.6.0';
  state.selectedPlannerDate = state.selectedPlannerDate || plannerToday();
  state.plannerPreferences = state.plannerPreferences || { workday_start:'08:30', workday_end:'17:00', lunch_start:'12:00', lunch_end:'13:00', focus_block_minutes:90, auto_schedule_blocked:false };
  state.calendarEvents = state.calendarEvents || defaultCalendarEvents(state.selectedPlannerDate);
  state.plannerBlocks = state.plannerBlocks || [];
  state.plannerRisks = state.plannerRisks || [];
  state.plannerMetrics = state.plannerMetrics || { scheduledBlocks: 0, aiScheduled: 0, meetings: state.calendarEvents.length, candidateTasks: state.tasks.filter(t=>t.status!=='DONE').length, freeSlotsRemaining: 0 };
}
function defaultCalendarEvents(day) {
  return [
    { id:'ce_standup', title:'Daily standup', kind:'meeting', startAt:`${day}T09:00:00`, endAt:`${day}T09:30:00`, source:'seed', color:'blue', ownerId:'adrian' },
    { id:'ce_focus', title:'Protected deep work', kind:'focus', startAt:`${day}T10:00:00`, endAt:`${day}T11:30:00`, source:'seed', color:'purple', ownerId:'adrian' },
    { id:'ce_stakeholder', title:'Stakeholder sync', kind:'meeting', startAt:`${day}T13:30:00`, endAt:`${day}T14:15:00`, source:'seed', color:'blue', ownerId:'adrian' },
    { id:'ce_triage', title:'Project risk triage', kind:'meeting', startAt:`${day}T15:30:00`, endAt:`${day}T16:00:00`, source:'seed', color:'orange', ownerId:'adrian' },
  ];
}
function renderPlannerSidebar() {
  ensurePlannerState();
  const day = state.selectedPlannerDate;
  return baseSidebar('Planner', "addFocusBlock()", `
    <div class="side-nav">
      <div class="side-item active" onclick="setPlannerDate('${plannerToday()}')"><span>▣</span><span>Today</span></div>
      <div class="side-item" onclick="shiftPlannerDate(1)"><span>☰</span><span>Tomorrow</span></div>
      <div class="side-item" onclick="addFocusBlock()"><span>◷</span><span>Focus Blocks</span></div>
      <div class="side-item" onclick="planMyDay()"><span>✽</span><span>AI Schedule</span></div>
    </div>
    <div class="hr"></div>
    <div class="side-section">Selected day</div>
    <div class="planner-mini-date"><input type="date" value="${day}" onchange="setPlannerDate(this.value)"/><button class="btn-secondary btn-small" onclick="refreshPlannerFromApi()">Sync</button></div>
    <div class="side-section">Calendars</div>
    <div class="side-item"><span>🟣</span><span>Work Tasks</span><small>${(state.plannerBlocks||[]).filter(b=>samePlannerDay(b.startAt)).length}</small></div>
    <div class="side-item"><span>🔵</span><span>Meetings</span><small>${(state.calendarEvents||[]).filter(e=>samePlannerDay(e.startAt) && e.kind==='meeting').length}</small></div>
    <div class="side-item"><span>🟢</span><span>Goals</span><small>${state.goals.length}</small></div>
    <div class="hr"></div>
    <div class="side-section">Planner controls</div>
    <button class="sidebar-wide-btn" onclick="planMyDay()">✽ Plan my day</button>
    <button class="sidebar-wide-btn" onclick="addCalendarMeetingDemo()">＋ Add meeting</button>
    <button class="sidebar-wide-btn" onclick="clearAISchedule()">Clear AI blocks</button>
  `);
}
function samePlannerDay(iso) { return String(iso||'').slice(0,10) === state.selectedPlannerDate; }
function plannerTime(iso) { try { return new Date(String(iso).replace(/:00$/, '')).toLocaleTimeString([], {hour:'numeric', minute:'2-digit'}); } catch { return String(iso).slice(11,16); } }
function plannerDuration(startAt, endAt) { try { return Math.max(0, Math.round((new Date(endAt) - new Date(startAt))/60000)); } catch { return 0; } }
function plannerDateLabel(day) { try { return new Date(day + 'T00:00:00').toLocaleDateString(undefined,{weekday:'long', month:'short', day:'numeric'}); } catch { return day; } }
function priorityScoreLocal(t) { const base = {Urgent:100, High:75, Normal:45, Low:20}[t.priority] || 35; const critical=t.critical?18:0; const blocked=t.status==='BLOCKED'?-50:0; let due=0; try { const diff=(new Date(t.due+'T00:00:00')-new Date(state.selectedPlannerDate+'T00:00:00'))/86400000; due=diff<0?35:diff<=1?25:diff<=3?12:0; } catch{} return Math.max(0, base+critical+blocked+due+(t.progress>50?5:0)); }
function plannerCandidateTasks() { return state.tasks.filter(t=>t.status!=='DONE' && (state.plannerPreferences.auto_schedule_blocked || t.status!=='BLOCKED')).sort((a,b)=>priorityScoreLocal(b)-priorityScoreLocal(a)); }
function renderPlannerMain() {
  ensurePlannerState();
  const day = state.selectedPlannerDate;
  const events = (state.calendarEvents||[]).filter(e=>samePlannerDay(e.startAt));
  const blocks = (state.plannerBlocks||[]).filter(b=>samePlannerDay(b.startAt));
  const candidates = plannerCandidateTasks();
  const timeline = [...events.map(e=>({...e, itemType:'event'})), ...blocks.map(b=>({...b, itemType:'block'}))].sort((a,b)=>String(a.startAt).localeCompare(String(b.startAt)));
  const focusMinutes = timeline.filter(x=>x.kind==='focus' || x.blockType==='focus' || x.blockType==='ai_task' || x.blockType==='task').reduce((sum,x)=>sum+plannerDuration(x.startAt,x.endAt),0);
  const risks = state.plannerRisks?.length ? state.plannerRisks : computePlannerRisksLocal(candidates, blocks);
  return `<div class="content wide">
    <div class="section-title"><div><h2>AI Planner + Scheduling Engine</h2><p style="margin:4px 0 0;color:var(--muted)">Tasks and meetings converge into a priority-based daily schedule with focus blocks, delay flags, and one-click schedule actions.</p></div><div><button class="btn-secondary" onclick="refreshPlannerFromApi()">⟳ Refresh</button><button class="btn-primary" onclick="planMyDay()">✽ Plan my day</button></div></div>
    <div class="planner-controlbar">
      <button class="pill-control" onclick="shiftPlannerDate(-1)">← Previous</button>
      <input type="date" value="${day}" onchange="setPlannerDate(this.value)" />
      <button class="pill-control" onclick="shiftPlannerDate(1)">Next →</button>
      <span class="report-status">${plannerDateLabel(day)} • ${apiOnline ? 'Server planner API available' : 'Local planner fallback'}</span>
    </div>
    <div class="cards-grid planner-kpis">
      <div class="kpi-card"><span class="badge purple">AI</span><h3>Scheduled blocks</h3><div class="value">${blocks.length}</div><div class="trend">${blocks.filter(b=>b.blockType==='ai_task').length} generated by AI today</div></div>
      <div class="kpi-card"><span class="badge green">Calendar</span><h3>Meetings</h3><div class="value">${events.filter(e=>e.kind==='meeting').length}</div><div class="trend">${events.length} total calendar items</div></div>
      <div class="kpi-card"><span class="badge">Focus</span><h3>Planned focus</h3><div class="value">${Math.round(focusMinutes/60*10)/10}h</div><div class="trend">Tasks, protected focus, and AI schedule blocks</div></div>
      <div class="kpi-card"><span class="badge ${risks.some(r=>r.level==='high')?'red':'warn'}">Risk</span><h3>Planner warnings</h3><div class="value">${risks.length}</div><div class="trend">AI delay and overload checks</div></div>
    </div>
    <div class="planner-layout-v06">
      <div class="report-card"><div class="report-card-head"><h3>Priority queue</h3><button class="btn-secondary btn-small" onclick="planMyDay()">Auto-place</button></div>
        <div class="priority-list">${candidates.slice(0,9).map(t=>`<div class="planner-task-card ${t.status==='BLOCKED'?'blocked':''}" onclick="openTask('${t.id}')"><div><b>${escapeHtml(t.name)}</b><div class="task-meta"><span>${escapeHtml(t.priority)}</span><span>${dateShort(t.due)}</span><span>${escapeHtml(memberById(t.assignee).name)}</span><span>${t.estimate || 1}h</span></div><div class="planner-score">Score ${Math.round(priorityScoreLocal(t))} • ${t.critical?'critical path':'standard'}</div></div><button class="btn-secondary btn-small" onclick="event.stopPropagation(); quickScheduleTask('${t.id}')">Schedule</button></div>`).join('')}</div>
      </div>
      <div class="report-card planner-day-card"><div class="report-card-head"><h3>Today timeline</h3><button class="btn-secondary btn-small" onclick="addFocusBlock()">＋ Focus</button></div>
        <div class="planner-timeline-v06">${timeline.length ? timeline.map(item=>renderPlannerTimelineItem(item)).join('') : `<div class="empty-mini">No blocks yet. Click <b>Plan my day</b> to generate a schedule.</div>`}</div>
      </div>
      <div class="report-card"><div class="report-card-head"><h3>AI delay watch</h3><button class="btn-secondary btn-small" onclick="runAISuggest('Planner risk review')">Ask AI</button></div>
        ${risks.map(r=>`<div class="planner-risk ${r.level}"><b>${escapeHtml(r.title)}</b><p>${escapeHtml(r.recommendation)}</p></div>`).join('') || `<div class="planner-risk low"><b>No major schedule warnings</b><p>Your planned work fits the current day.</p></div>`}
        <div class="hr"></div><h3>Scheduling rules</h3>
        <div class="planner-pref-row"><span>Workday</span><b>${state.plannerPreferences.workday_start || '08:30'}–${state.plannerPreferences.workday_end || '17:00'}</b></div>
        <div class="planner-pref-row"><span>Focus block size</span><b>${state.plannerPreferences.focus_block_minutes || 90} min</b></div>
        <div class="planner-pref-row"><span>Blocked tasks</span><b>${state.plannerPreferences.auto_schedule_blocked ? 'Include' : 'Exclude'}</b></div>
      </div>
    </div>
    <div class="section-title"><h2>Week strip</h2><button class="btn-secondary" onclick="toast('Week optimization placeholder')">Optimize week</button></div>
    <div class="planner-week-strip">${[0,1,2,3,4,5,6].map(offset=>renderWeekDay(offset)).join('')}</div>
  </div>`;
}
function renderPlannerTimelineItem(item) {
  const isEvent = item.itemType === 'event';
  const cls = isEvent ? `event ${item.kind||'meeting'}` : `block ${item.blockType||'task'}`;
  const title = item.title || item.name;
  const meta = isEvent ? `${item.kind || 'event'} • ${item.source || 'manual'}` : `${item.blockType || 'task'} • ${item.reason || 'scheduled work'}`;
  const actions = isEvent ? `<button class="btn-secondary btn-small" onclick="toast('Calendar event opened')">Open</button>` : `<button class="btn-secondary btn-small" onclick="openTask('${item.taskId||''}')">Task</button><button class="btn-secondary btn-small" onclick="removePlannerBlock('${item.id}')">Remove</button>`;
  return `<div class="planner-time-row ${cls}"><div class="planner-time"><b>${plannerTime(item.startAt)}</b><span>${plannerTime(item.endAt)}</span></div><div class="planner-time-body"><b>${escapeHtml(title)}</b><p>${escapeHtml(meta)}</p></div><div class="planner-time-actions">${actions}</div></div>`;
}
function renderWeekDay(offset){ const d=new Date(state.selectedPlannerDate+'T00:00:00'); d.setDate(d.getDate()+offset); const key=d.toISOString().slice(0,10); const count=(state.plannerBlocks||[]).filter(b=>String(b.startAt||'').slice(0,10)===key).length; return `<button class="week-day ${key===state.selectedPlannerDate?'active':''}" onclick="setPlannerDate('${key}')"><b>${d.toLocaleDateString(undefined,{weekday:'short'})}</b><span>${d.toLocaleDateString(undefined,{month:'short',day:'numeric'})}</span><em>${count} blocks</em></button>`; }
function computePlannerRisksLocal(tasks, blocks){ const risks=[]; const overdue=tasks.filter(t=>t.due && t.due<state.selectedPlannerDate).length; const blocked=state.tasks.filter(t=>t.status==='BLOCKED').length; if(overdue) risks.push({level:'high',title:`${overdue} overdue tasks need recovery`,recommendation:'Schedule recovery time or renegotiate due dates.'}); if(blocked) risks.push({level:'medium',title:`${blocked} blocked tasks need clearing`,recommendation:'Resolve blockers before AI can safely schedule execution work.'}); if(blocks.length<3) risks.push({level:'medium',title:'Schedule is under-planned',recommendation:'Run Plan my day or drag priority work into focus blocks.'}); return risks; }
async function refreshPlannerFromApi(){ ensurePlannerState(); if(!apiOnline){ toast('Planner running locally'); render(); return; } try{ const res=await fetch(`${API_BASE}/planner?date=${state.selectedPlannerDate}`, {headers: authHeaders(), cache:'no-store'}); if(!res.ok) throw new Error('Planner API failed'); const data=await res.json(); applyPlannerPayload(data); toast('Planner refreshed from API'); saveState(); render(); }catch(err){ console.warn(err); toast('Planner API unavailable; using local schedule'); }}
function applyPlannerPayload(data){ if(data.state){ state={...state,...data.state}; ensurePlannerState(); return; } if(data.events) state.calendarEvents=[...(state.calendarEvents||[]).filter(e=>!samePlannerDay(e.startAt)),...data.events]; if(data.blocks) state.plannerBlocks=[...(state.plannerBlocks||[]).filter(b=>!samePlannerDay(b.startAt)),...data.blocks]; if(data.risks) state.plannerRisks=data.risks; if(data.metrics) state.plannerMetrics=data.metrics; if(data.preferences) state.plannerPreferences={...state.plannerPreferences,...data.preferences}; }
async function planMyDay(){ ensurePlannerState(); if(apiOnline){ try{ const res=await fetch(`${API_BASE}/planner/plan-my-day`, {method:'POST', headers:{'Content-Type':'application/json', ...authHeaders()}, body: JSON.stringify({date: state.selectedPlannerDate, owner_id:'adrian', mode:'balanced', regenerate:true})}); if(!res.ok) throw new Error('Planner API failed'); const data=await res.json(); applyPlannerPayload(data); toast(`AI scheduled ${data.metrics?.aiScheduled || 0} blocks`); saveState(); render(); return; }catch(err){ console.warn(err); toast('Planner API unavailable; generating locally'); }} generatePlannerBlocksLocal(); saveState(); render(); }
function generatePlannerBlocksLocal(){ const day=state.selectedPlannerDate; const candidates=plannerCandidateTasks(); const slots=['08:30','09:30','11:30','13:00','14:20','16:00']; state.plannerBlocks=(state.plannerBlocks||[]).filter(b=>!(samePlannerDay(b.startAt)&&b.blockType==='ai_task')); candidates.slice(0,6).forEach((t,i)=>{ const start=slots[i]||'16:00'; const duration=Math.min(90, Math.max(30, Math.round((t.estimate||1)*60))); state.plannerBlocks.push({id:uid(), taskId:t.id, title:t.name, ownerId:t.assignee, startAt:`${day}T${start}:00`, endAt:addMinutesIso(`${day}T${start}:00`, duration), blockType:'ai_task', status:'planned', score:priorityScoreLocal(t), reason:`AI scheduled from priority ${t.priority}${t.critical?', critical path':''}`}); }); state.plannerRisks=computePlannerRisksLocal(candidates,state.plannerBlocks); state.plannerMetrics={scheduledBlocks:state.plannerBlocks.filter(b=>samePlannerDay(b.startAt)).length, aiScheduled:state.plannerBlocks.filter(b=>samePlannerDay(b.startAt)&&b.blockType==='ai_task').length, meetings:state.calendarEvents.filter(e=>samePlannerDay(e.startAt)).length, candidateTasks:candidates.length}; toast(`AI scheduled ${state.plannerMetrics.aiScheduled} local blocks`); }
function addMinutesIso(iso, minutes){ const d=new Date(iso); d.setMinutes(d.getMinutes()+minutes); return d.toISOString().slice(0,19); }
function setPlannerDate(day){ state.selectedPlannerDate=day || plannerToday(); ensurePlannerState(); render(); }
function shiftPlannerDate(days){ const d=new Date(state.selectedPlannerDate+'T00:00:00'); d.setDate(d.getDate()+days); setPlannerDate(d.toISOString().slice(0,10)); }
async function quickScheduleTask(taskId){ ensurePlannerState(); const open=['08:30','11:30','14:30','16:00']; const existing=(state.plannerBlocks||[]).filter(b=>samePlannerDay(b.startAt)).length; const time=open[Math.min(existing, open.length-1)]; const task=state.tasks.find(t=>t.id===taskId); if(!task) return; if(apiOnline){ try{ const res=await fetch(`${API_BASE}/planner/tasks/${taskId}/schedule`, {method:'POST', headers:{'Content-Type':'application/json', ...authHeaders()}, body: JSON.stringify({date:state.selectedPlannerDate, start_time:time, duration_minutes:Math.min(90, Math.max(30, Math.round((task.estimate||1)*60))), owner_id:task.assignee, reason:'Quick scheduled from Planner priority queue'})}); if(res.ok){ const data=await res.json(); applyPlannerPayload(data); toast('Task scheduled'); saveState(); render(); return; }}catch(err){ console.warn(err); }} state.plannerBlocks.push({id:uid(), taskId:task.id, title:task.name, ownerId:task.assignee, startAt:`${state.selectedPlannerDate}T${time}:00`, endAt:addMinutesIso(`${state.selectedPlannerDate}T${time}:00`,60), blockType:'task', status:'planned', score:priorityScoreLocal(task), reason:'Quick scheduled locally'}); toast('Task scheduled locally'); saveState(); render(); }
async function addFocusBlock(){ ensurePlannerState(); const start='10:00'; if(apiOnline){ try{ const res=await fetch(`${API_BASE}/planner/focus-blocks`, {method:'POST', headers:{'Content-Type':'application/json', ...authHeaders()}, body: JSON.stringify({date:state.selectedPlannerDate, start_time:start, duration_minutes:90, title:'Protected focus block', owner_id:'adrian', reason:'Created from Planner UI'})}); if(res.ok){ const data=await res.json(); applyPlannerPayload(data); toast('Focus block created'); saveState(); render(); return; }}catch(err){ console.warn(err); }} state.plannerBlocks.push({id:uid(), taskId:null, title:'Protected focus block', ownerId:'adrian', startAt:`${state.selectedPlannerDate}T${start}:00`, endAt:addMinutesIso(`${state.selectedPlannerDate}T${start}:00`,90), blockType:'focus', status:'protected', score:0, reason:'Created locally'}); toast('Focus block created locally'); saveState(); render(); }
async function removePlannerBlock(blockId){ if(!blockId) return; if(apiOnline){ try{ const res=await fetch(`${API_BASE}/planner/blocks/${blockId}`, {method:'DELETE', headers:authHeaders()}); if(res.ok){ const data=await res.json(); if(data.state) state={...state,...data.state}; toast('Planner block removed'); saveState(); render(); return; }}catch(err){ console.warn(err); }} state.plannerBlocks=(state.plannerBlocks||[]).filter(b=>b.id!==blockId); toast('Planner block removed locally'); saveState(); render(); }
function clearAISchedule(){ state.plannerBlocks=(state.plannerBlocks||[]).filter(b=>!(samePlannerDay(b.startAt)&&b.blockType==='ai_task')); toast('AI schedule blocks cleared'); saveState(); render(); }
async function addCalendarMeetingDemo(){ ensurePlannerState(); const event={title:'New planning sync', kind:'meeting', start_at:`${state.selectedPlannerDate}T14:00:00`, end_at:`${state.selectedPlannerDate}T14:30:00`, source:'manual', owner_id:'adrian', color:'blue', metadata:{created_from:'planner_ui'}}; if(apiOnline){ try{ const res=await fetch(`${API_BASE}/planner/events`, {method:'POST', headers:{'Content-Type':'application/json', ...authHeaders()}, body: JSON.stringify(event)}); if(res.ok){ const data=await res.json(); applyPlannerPayload(data); toast('Meeting added'); saveState(); render(); return; }}catch(err){ console.warn(err); }} state.calendarEvents.push({id:uid(), title:event.title, kind:event.kind, startAt:event.start_at, endAt:event.end_at, source:'manual', ownerId:'adrian', color:'blue'}); toast('Meeting added locally'); saveState(); render(); }
function renderDataLayerCards() {
  const tasks = state.tasks.length;
  const projects = state.spaces.flatMap(s => s.folders || []).flatMap(f => f.lists || []).filter(l => l.kind === 'project').length;
  const comments = state.tasks.reduce((sum, t) => sum + (t.comments?.length || 0), 0);
  const submissions = (state.formSubmissions || []).length;
  const runs = (state.automationRuns || []).length;
  const blocks = (state.plannerBlocks || []).length;
  const events = (state.calendarEvents || []).length;
  return `<div class="cards-grid">
    <div class="kpi-card"><span class="badge ${apiOnline ? 'green' : 'warn'}">${apiOnline ? 'Online' : 'Offline fallback'}</span><h3>v0.9 Visual Collaboration</h3><div class="value">${apiOnline ? 'API' : 'Local'}</div><div class="trend">${apiStatusText}</div><button class="btn-secondary" onclick="showDataLayerStatus()">Check status</button></div>
    <div class="kpi-card"><h3>Persisted tasks</h3><div class="value">${tasks}</div><div class="trend">${projects} projects • ${comments} comments • scheduling enabled</div><button class="btn-secondary" onclick="syncStateToApi(); toast('Manual sync requested')">Sync now</button></div>
    <div class="kpi-card"><span class="badge purple">Planner</span><h3>Schedule objects</h3><div class="value">${blocks + events}</div><div class="trend">${blocks} planner blocks • ${events} calendar events</div><button class="btn-secondary" onclick="setModule('planner')">Open planner</button></div>
    <div class="kpi-card"><span class="badge green">Automation</span><h3>Run history</h3><div class="value">${runs}</div><div class="trend">Forms ${submissions} • /api/docs, /api/knowledge, /api/gantt, /api/planner</div><button class="btn-secondary" onclick="window.open('/api/docs','_blank')">Open API docs</button></div>
  </div>`;
}



/* v0.9 Visual Collaboration / Whiteboards + Canvas + Mind Maps */
function defaultWhiteboardSeed(){
  return [{
    id:'wb1', name:'Launch Planning Board', icon:'✎', owner:'Adrian Francis', updated:'Today', favorite:true,
    objects:[
      {id:'wbo1', type:'sticky', text:'Project idea\n\nAI turns this into a project plan.', color:'yellow', x:72, y:86, w:180, h:126, taskId:null},
      {id:'wbo2', type:'sticky', text:'Dashboard card\n\nLive KPI with task drill-down.', color:'blue', x:330, y:164, w:184, h:126, taskId:'t4'},
      {id:'wbo3', type:'sticky', text:'Form intake\n\nCentralize requests and trigger workflows.', color:'pink', x:562, y:92, w:190, h:126, taskId:'t5'},
      {id:'wbo4', type:'sticky', text:'Automation\n\nEscalate blocked work automatically.', color:'green', x:790, y:236, w:190, h:126, taskId:null},
      {id:'wbo5', type:'task', text:'Campaign dashboard wireframe', color:'purple', x:314, y:356, w:248, h:96, taskId:'t4'},
      {id:'wbo6', type:'doc', text:'Project Charter', color:'white', x:90, y:310, w:220, h:92, docId:'doc1'}
    ],
    edges:[
      {id:'edge1', from:'wbo1', to:'wbo2', label:'plan'},
      {id:'edge2', from:'wbo2', to:'wbo3', label:'insight'},
      {id:'edge3', from:'wbo3', to:'wbo4', label:'trigger'},
      {id:'edge4', from:'wbo1', to:'wbo6', label:'document'},
      {id:'edge5', from:'wbo2', to:'wbo5', label:'work item'}
    ],
    canvasCards:[
      {id:'cc1', title:'Execution Hub', kind:'Project', metric:'8 tasks', x:40, y:40, linkedType:'list', linkedId:'p1'},
      {id:'cc2', title:'AI Risk Watch', kind:'AI Card', metric:'2 risks', x:322, y:46, linkedType:'dashboard', linkedId:'d1'},
      {id:'cc3', title:'Intake Flow', kind:'Form', metric:'3 submissions', x:606, y:48, linkedType:'form', linkedId:'form1'},
      {id:'cc4', title:'Knowledge Base', kind:'Docs', metric:'3 docs', x:178, y:250, linkedType:'doc', linkedId:'doc1'},
      {id:'cc5', title:'Critical Path', kind:'Gantt', metric:'3 critical tasks', x:486, y:250, linkedType:'gantt', linkedId:'p1'}
    ],
    mindMap:{
      root:{id:'mm-root', label:'Thing Planner WorkOS', kind:'root'},
      nodes:[
        {id:'mm-tasks', parent:'mm-root', label:'Tasks & Projects', kind:'module', linkedType:'module', linkedId:'spaces'},
        {id:'mm-reports', parent:'mm-root', label:'Reports & Dashboards', kind:'module', linkedType:'module', linkedId:'dashboards'},
        {id:'mm-ai', parent:'mm-root', label:'AI Agents', kind:'module', linkedType:'module', linkedId:'ai'},
        {id:'mm-forms', parent:'mm-root', label:'Forms + Intake', kind:'module', linkedType:'module', linkedId:'forms'},
        {id:'mm-docs', parent:'mm-root', label:'Docs + Decisions', kind:'module', linkedType:'module', linkedId:'docs'},
        {id:'mm-gantt', parent:'mm-tasks', label:'Critical Path', kind:'feature', linkedType:'view', linkedId:'gantt'},
        {id:'mm-board', parent:'mm-tasks', label:'Kanban Board', kind:'feature', linkedType:'view', linkedId:'board'},
        {id:'mm-ai-summary', parent:'mm-ai', label:'Status Reports', kind:'feature', linkedType:'action', linkedId:'ai-summary'},
        {id:'mm-submissions', parent:'mm-forms', label:'Task Creation', kind:'feature', linkedType:'action', linkedId:'form-task'},
        {id:'mm-decisions', parent:'mm-docs', label:'Decision Records', kind:'feature', linkedType:'action', linkedId:'decisions'}
      ]
    }
  }];
}
function ensureWhiteboardState(){
  if(!state.whiteboards || !Array.isArray(state.whiteboards) || state.whiteboards.length===0) state.whiteboards=defaultWhiteboardSeed();
  if(!state.selectedWhiteboard) state.selectedWhiteboard=state.whiteboards[0]?.id || 'wb1';
  if(!state.visualTab) state.visualTab='whiteboard';
  if(!state.whiteboardAiInsights) state.whiteboardAiInsights=[];
}
function selectedWhiteboard(){ ensureWhiteboardState(); return state.whiteboards.find(w=>w.id===state.selectedWhiteboard) || state.whiteboards[0]; }
function setVisualTab(tab){ state.visualTab=tab; render(); }
function selectWhiteboard(id){ state.selectedWhiteboard=id; render(); }
function whiteboardStats(w){
  const objects=w.objects||[], edges=w.edges||[], cards=w.canvasCards||[], nodes=w.mindMap?.nodes||[];
  const linkedTasks=objects.filter(o=>o.taskId).length + cards.filter(c=>c.linkedType==='task').length;
  return {objects:objects.length, edges:edges.length, canvasCards:cards.length, mindNodes:nodes.length+1, linkedTasks};
}
function renderWhiteboardsMain() {
  ensureWhiteboardState();
  const w=selectedWhiteboard(); const stats=whiteboardStats(w);
  return `<div class="content wide">
    <div class="section-title"><div><h2>Visual Collaboration</h2><p style="margin:4px 0 0;color:var(--muted)">Whiteboards, canvas planning, and mind maps that convert ideas into coordinated action.</p></div><div class="toolbar-right"><button class="btn-secondary" onclick="refreshWhiteboardsFromApi()">Refresh</button><button class="btn-secondary" onclick="runWhiteboardAI()">✽ AI summarize</button><button class="btn-primary" onclick="addSticky()">＋ Sticky</button></div></div>
    <div class="visual-kpis">
      ${visualKpi('Objects', stats.objects, 'sticky notes, tasks, docs')}
      ${visualKpi('Connected edges', stats.edges, 'relationships mapped')}
      ${visualKpi('Canvas cards', stats.canvasCards, 'live planning blocks')}
      ${visualKpi('Mind map nodes', stats.mindNodes, 'hierarchy concepts')}
    </div>
    <div class="visual-shell">
      <div class="visual-board-list">
        <div class="visual-board-head">Boards <button class="icon-btn flat" onclick="createWhiteboard()">＋</button></div>
        ${(state.whiteboards||[]).map(b=>`<button class="visual-board-row ${b.id===w.id?'active':''}" onclick="selectWhiteboard('${b.id}')"><span>${b.icon||'✎'}</span><span><b>${escapeHtml(b.name)}</b><em>${(b.objects||[]).length} objects • ${b.updated||'Today'}</em></span></button>`).join('')}
        <div class="visual-ai-card"><b>✽ AI board readout</b><p>${escapeHtml((state.whiteboardAiInsights||[])[0]?.summary || 'Run AI summarize to turn this board into tasks, risks, and decisions.')}</p></div>
      </div>
      <div class="visual-workspace">
        <div class="visual-tabs">
          <button class="tab ${state.visualTab==='whiteboard'?'active':''}" onclick="setVisualTab('whiteboard')">✎ Whiteboard</button>
          <button class="tab ${state.visualTab==='canvas'?'active':''}" onclick="setVisualTab('canvas')">▧ Canvas</button>
          <button class="tab ${state.visualTab==='mindmap'?'active':''}" onclick="setVisualTab('mindmap')">🧠 Mind Map</button>
          <button class="tab" onclick="convertStickyToTask()">☑ Convert to task</button>
        </div>
        ${state.visualTab==='canvas' ? renderCanvasStudio(w) : state.visualTab==='mindmap' ? renderMindMapStudio(w) : renderWhiteboardStudio(w)}
      </div>
    </div>
  </div>`;
}
function visualKpi(label,value,trend){ return `<div class="kpi-card visual-kpi"><span class="label">${escapeHtml(label)}</span><div class="value">${value}</div><div class="trend">${escapeHtml(trend)}</div></div>`; }
function renderWhiteboardStudio(w){
  return `<div class="whiteboard-canvas v09">
    ${(w.edges||[]).map(e=>renderWhiteboardEdge(w,e)).join('')}
    ${(w.objects||[]).map(o=>renderWhiteboardObject(o)).join('')}
    <div class="whiteboard-toolbar"><button onclick="addSticky()">Sticky</button><button onclick="linkObjectToTask()">Link task</button><button onclick="runWhiteboardAI()">AI actions</button></div>
  </div>`;
}
function renderWhiteboardObject(o){
  const style=`left:${Number(o.x||0)}px;top:${Number(o.y||0)}px;width:${Number(o.w||180)}px;min-height:${Number(o.h||110)}px`;
  const task=o.taskId ? state.tasks.find(t=>t.id===o.taskId) : null;
  return `<div class="visual-object ${escapeHtml(o.type||'sticky')} ${escapeHtml(o.color||'yellow')}" style="${style}" onclick="selectVisualObject('${o.id}')"><div class="visual-object-type">${objectIcon(o.type)} ${escapeHtml(o.type||'sticky')}</div><b>${escapeHtml(firstLine(o.text))}</b><p>${escapeHtml(restLines(o.text))}</p>${task?`<button class="mini-link" onclick="event.stopPropagation(); openTask('${task.id}')">☑ ${escapeHtml(task.name)}</button>`:''}</div>`;
}
function renderWhiteboardEdge(w,e){
  const from=(w.objects||[]).find(o=>o.id===e.from), to=(w.objects||[]).find(o=>o.id===e.to); if(!from||!to) return '';
  const x1=Number(from.x||0)+Number(from.w||180), y1=Number(from.y||0)+Number(from.h||110)/2, x2=Number(to.x||0), y2=Number(to.y||0)+Number(to.h||110)/2;
  const dx=x2-x1, dy=y2-y1, len=Math.max(28, Math.sqrt(dx*dx+dy*dy)), angle=Math.atan2(dy,dx)*180/Math.PI;
  return `<div class="visual-edge" style="left:${x1}px;top:${y1}px;width:${len}px;transform:rotate(${angle}deg)"><span>${escapeHtml(e.label||'')}</span></div>`;
}
function renderCanvasStudio(w){
  return `<div class="canvas-studio"><div class="canvas-actions"><button class="btn-secondary btn-small" onclick="addCanvasCard()">＋ Live card</button><button class="btn-secondary btn-small" onclick="toast('Canvas layout saved')">Save layout</button></div>${(w.canvasCards||[]).map(c=>`<div class="canvas-card" style="left:${c.x}px;top:${c.y}px" onclick="openCanvasLink('${c.linkedType}','${c.linkedId}')"><span class="badge purple">${escapeHtml(c.kind)}</span><h3>${escapeHtml(c.title)}</h3><div class="value">${escapeHtml(c.metric)}</div><p>${escapeHtml(c.linkedType)} / ${escapeHtml(c.linkedId)}</p></div>`).join('')}</div>`;
}
function renderMindMapStudio(w){
  const nodes=w.mindMap?.nodes||[]; const root=w.mindMap?.root||{id:'root',label:w.name};
  const first=nodes.filter(n=>n.parent===root.id); const children=id=>nodes.filter(n=>n.parent===id);
  return `<div class="mindmap-studio"><div class="mind-root">${escapeHtml(root.label)}</div><div class="mind-branches">${first.map((n,i)=>`<div class="mind-branch"><button class="mind-node ${n.kind}" onclick="openCanvasLink('${n.linkedType}','${n.linkedId}')">${escapeHtml(n.label)}</button><div class="mind-children">${children(n.id).map(ch=>`<button class="mind-node child" onclick="openCanvasLink('${ch.linkedType}','${ch.linkedId}')">${escapeHtml(ch.label)}</button>`).join('')}</div></div>`).join('')}</div></div>`;
}
function objectIcon(type){ return {sticky:'▨', task:'☑', doc:'▤', decision:'◆'}[type] || '▨'; }
function firstLine(text){ return String(text||'').split('\n')[0] || 'Untitled'; }
function restLines(text){ const parts=String(text||'').split('\n').slice(1).join(' ').trim(); return parts || 'Add context, then convert this idea into work.'; }
function selectVisualObject(id){ state.selectedVisualObject=id; toast('Selected visual object'); saveState(); }
function createWhiteboard(){ ensureWhiteboardState(); const id=uid(); state.whiteboards.unshift({id, name:`New Strategy Board ${state.whiteboards.length+1}`, icon:'✎', owner:'Adrian Francis', updated:'Now', favorite:false, objects:[], edges:[], canvasCards:[], mindMap:{root:{id:'root',label:'New Strategy'},nodes:[]}}); state.selectedWhiteboard=id; saveState(); render(); toast('Whiteboard created'); }
function addSticky(){ const w=selectedWhiteboard(); const id=uid(); w.objects=w.objects||[]; w.objects.push({id,type:'sticky',text:'New idea\n\nClick AI summarize or convert to task.',color:['yellow','blue','pink','green'][w.objects.length%4],x:90+(w.objects.length*42)%650,y:80+(w.objects.length*58)%330,w:182,h:126}); w.updated='Now'; saveState(); render(); toast('Sticky note added'); }
function addCanvasCard(){ const w=selectedWhiteboard(); w.canvasCards=w.canvasCards||[]; w.canvasCards.push({id:uid(),title:'Live Work Card',kind:'Task Rollup',metric:`${state.tasks.filter(t=>t.status!=='DONE').length} open`,x:80+(w.canvasCards.length*60)%540,y:100+(w.canvasCards.length*72)%300,linkedType:'dashboard',linkedId:'d1'}); w.updated='Now'; saveState(); render(); toast('Canvas card added'); }
function convertStickyToTask(){ const w=selectedWhiteboard(); const obj=(w.objects||[]).find(o=>o.id===state.selectedVisualObject) || (w.objects||[]).find(o=>o.type==='sticky'&&!o.taskId) || (w.objects||[])[0]; if(!obj){ toast('Add a sticky note first'); return; } const title=firstLine(obj.text); const task={id:uid(), projectId:state.selectedProject||'p1', name:title, assignee:'adrian', due:new Date(Date.now()+86400000*5).toISOString().slice(0,10), priority:'Normal', status:'TO DO', comments:[{by:'WorkMind',text:'Created from v0.9 visual collaboration board.'}], estimate:2, tracked:0, billable:false, tags:['Whiteboard'], progress:0, description:restLines(obj.text), start:new Date().toISOString().slice(0,10), duration:2, critical:false}; state.tasks.push(task); obj.taskId=task.id; w.updated='Now'; saveState(); render(); toast('Sticky converted to task'); }
function linkObjectToTask(){ const w=selectedWhiteboard(); const obj=(w.objects||[]).find(o=>o.id===state.selectedVisualObject) || (w.objects||[])[0]; const task=state.tasks.find(t=>t.status==='BLOCKED') || state.tasks.find(t=>t.status!=='DONE'); if(!obj||!task){ toast('Need an object and a task to link'); return; } obj.taskId=task.id; w.updated='Now'; saveState(); render(); toast(`Linked to ${task.name}`); }
function openCanvasLink(type,id){ if(type==='module'){ setModule(id); return; } if(type==='task'){ openTask(id); return; } if(type==='doc'){ state.selectedDoc=id; setModule('docs'); return; } if(type==='form'){ setModule('forms'); return; } if(type==='dashboard'){ setModule('dashboards'); return; } if(type==='gantt'||id==='gantt'){ state.module='spaces'; state.view='gantt'; render(); return; } toast(`${type || 'Link'} opened`); }
function localWhiteboardAI(w){ const stats=whiteboardStats(w); const blockers=state.tasks.filter(t=>t.status==='BLOCKED'); return {summary:`${w.name} has ${stats.objects} objects, ${stats.edges} relationships, ${stats.linkedTasks} linked task references, and ${stats.canvasCards} canvas cards. AI recommends converting unlinked ideas to tasks and reviewing ${blockers.length} blocker(s).`, actions:['Convert the highest-value sticky into a task','Link the Form Intake note to the project intake workflow','Review critical-path blockers before the next status report'], risks:blockers.map(t=>t.name).slice(0,3)}; }
async function runWhiteboardAI(){ const w=selectedWhiteboard(); if(apiOnline){ try{ const res=await fetch(`${API_BASE}/whiteboards/${w.id}/ai-summary`,{method:'POST',headers:authHeaders()}); if(res.ok){ const data=await res.json(); if(data.whiteboards) state.whiteboards=data.whiteboards; state.whiteboardAiInsights=[data.summary]; toast('AI visual summary generated'); saveState(); render(); return; }}catch(e){ console.warn(e); }} state.whiteboardAiInsights=[localWhiteboardAI(w)]; toast('AI visual summary generated locally'); saveState(); render(); }
async function refreshWhiteboardsFromApi(){ ensureWhiteboardState(); if(!apiOnline){ toast('Whiteboards running locally'); render(); return; } try{ const res=await fetch(`${API_BASE}/whiteboards`,{headers:authHeaders(),cache:'no-store'}); if(!res.ok) throw new Error('Whiteboard API failed'); const data=await res.json(); state.whiteboards=data.whiteboards||state.whiteboards; if(!state.selectedWhiteboard&&state.whiteboards[0]) state.selectedWhiteboard=state.whiteboards[0].id; toast('Whiteboards refreshed from API'); saveState(); render(); }catch(e){ console.warn(e); toast('Whiteboard API unavailable; using local boards'); } }


function showDataLayerStatus() {
  const message = apiOnline
    ? `Connected to the v0.9 visual collaboration API. ${authStatusText}. Last sync: ${lastSyncAt ? lastSyncAt.toLocaleTimeString() : 'just now'}.`
    : 'Running in local fallback mode. Start Docker Compose to enable FastAPI persistence for whiteboards, canvas cards, and mind maps.';
  toast(message);
}
function renderDataLayerCards() {
  ensureWhiteboardState();
  const tasks = state.tasks.length;
  const projects = state.spaces.flatMap(s => s.folders || []).flatMap(f => f.lists || []).filter(l => l.kind === 'project').length;
  const comments = state.tasks.reduce((sum, t) => sum + (t.comments?.length || 0), 0);
  const submissions = (state.formSubmissions || []).length;
  const runs = (state.automationRuns || []).length;
  const whiteboardCount = (state.whiteboards || []).length;
  const visualObjects = (state.whiteboards || []).reduce((sum,w)=>sum+(w.objects||[]).length+(w.canvasCards||[]).length+(w.mindMap?.nodes||[]).length,0);
  return `<div class="cards-grid">
    <div class="kpi-card"><span class="badge ${apiOnline ? 'green' : 'warn'}">${apiOnline ? 'Online' : 'Offline fallback'}</span><h3>v0.9 Visual Collaboration</h3><div class="value">${apiOnline ? 'API' : 'Local'}</div><div class="trend">${apiStatusText}</div><button class="btn-secondary" onclick="showDataLayerStatus()">Check status</button></div>
    <div class="kpi-card"><h3>Persisted tasks</h3><div class="value">${tasks}</div><div class="trend">${projects} projects • ${comments} comments • visual links enabled</div><button class="btn-secondary" onclick="syncStateToApi(); toast('Manual sync requested')">Sync now</button></div>
    <div class="kpi-card"><span class="badge purple">Whiteboards</span><h3>Visual objects</h3><div class="value">${visualObjects}</div><div class="trend">${whiteboardCount} boards • canvas cards and mind maps</div><button class="btn-secondary" onclick="setModule('whiteboards')">Open whiteboards</button></div>
    <div class="kpi-card"><span class="badge green">Automation</span><h3>Run history</h3><div class="value">${runs}</div><div class="trend">Forms ${submissions} • /api/whiteboards, /api/docs, /api/gantt</div><button class="btn-secondary" onclick="window.open('/api/docs','_blank')">Open API docs</button></div>
  </div>`;
}

window.setModule = setModule;
window.setView = setView;
window.selectProject = selectProject;
window.setHomeTab = setHomeTab;
window.markNotificationRead = markNotificationRead;
window.clearNotifications = clearNotifications;
window.quickAddTask = quickAddTask;
window.addTaskFromInput = addTaskFromInput;
window.updateTask = updateTask;
window.openTask = openTask;
window.closeTaskDrawer = closeTaskDrawer;
window.addComment = addComment;
window.dragTask = dragTask;
window.dropTask = dropTask;
window.runAI = runAI;
window.runAISuggest = runAISuggest;
window.createAITasks = createAITasks;
window.openFormBuilder = openFormBuilder;
window.submitFormDemo = submitFormDemo;
window.refreshFormsFromApi = refreshFormsFromApi;
window.saveFormSchemaDemo = saveFormSchemaDemo;
window.runManualAutomation = runManualAutomation;
window.createDashboard = createDashboard;
window.renderDashboardTemplatesOnly = renderDashboardTemplatesOnly;
window.setReportFilter = setReportFilter;
window.refreshReportDataset = refreshReportDataset;
window.addReportCard = addReportCard;
window.dashboardAction = dashboardAction;
window.drilldownReport = drilldownReport;
window.toggleAutomation = toggleAutomation;
window.planMyDay = planMyDay;

function ensureGanttState(){
  state.taskDependencies = state.taskDependencies || [];
  state.ganttRiskAlerts = state.ganttRiskAlerts || [];
  state.ganttBaselines = state.ganttBaselines || [];
  state.ganttMetrics = state.ganttMetrics || {};
}
function ganttDate(value){ const d = value ? new Date(String(value).slice(0,10)+'T00:00:00') : new Date(); return Number.isNaN(d.getTime()) ? new Date() : d; }
function ganttIso(d){ return d.toISOString().slice(0,10); }
function ganttAddDays(value, days){ const d=ganttDate(value); d.setDate(d.getDate()+Number(days||0)); return ganttIso(d); }
function ganttDayDiff(a,b){ return Math.round((ganttDate(b)-ganttDate(a))/(1000*60*60*24)); }
function taskEndDate(t){ return ganttAddDays(t.start || t.due, Math.max(1, Number(t.duration||1))); }
function taskById(id){ return state.tasks.find(t=>t.id===id); }
function ganttTicks(start, days){ const total=Math.max(4, Number(days||10)); const step=Math.max(1, Math.ceil(total/5)); const out=[]; for(let i=0;i<=total;i+=step){ const d=ganttDate(start); d.setDate(d.getDate()+i); out.push(d.toLocaleDateString(undefined,{month:'short',day:'numeric'})); } return out.slice(0,6); }
function computeLocalCriticalPath(tasks, deps){
  const byId=Object.fromEntries(tasks.map(t=>[t.id,t])); const succ={}; tasks.forEach(t=>succ[t.id]=[]); deps.forEach(d=>{ if(byId[d.predecessorId]&&byId[d.successorId]) (succ[d.predecessorId] ||= []).push(d.successorId); });
  const memo={}; const visiting=new Set();
  function best(id){ if(memo[id]) return memo[id]; if(visiting.has(id)) return {score:0,path:[id]}; visiting.add(id); const dur=Math.max(1,Number(byId[id]?.duration||1)); let bestScore=dur, bestPath=[id]; (succ[id]||[]).forEach(s=>{ const r=best(s); if(dur+r.score>bestScore){ bestScore=dur+r.score; bestPath=[id,...r.path]; }}); visiting.delete(id); memo[id]={score:bestScore,path:bestPath}; return memo[id]; }
  let top={score:0,path:[]}; tasks.forEach(t=>{ const r=best(t.id); if(r.score>top.score) top=r; });
  return [...new Set([...top.path, ...tasks.filter(t=>t.critical).map(t=>t.id)])];
}
function computeLocalGanttDataset(projectId){
  ensureGanttState(); const tasks=state.tasks.filter(t=>t.projectId===projectId); const ids=new Set(tasks.map(t=>t.id)); const deps=(state.taskDependencies||[]).filter(d=>ids.has(d.predecessorId)&&ids.has(d.successorId));
  const criticalPath=computeLocalCriticalPath(tasks,deps); const starts=tasks.map(t=>ganttDate(t.start||t.due)); const ends=tasks.map(t=>ganttDate(taskEndDate(t))); const min=new Date(Math.min(...starts.map(d=>d.getTime()), Date.now())); const max=new Date(Math.max(...ends.map(d=>d.getTime()), Date.now()+7*86400000)); const timeline={start:ganttIso(min), end:ganttIso(max), days:Math.max(1,ganttDayDiff(ganttIso(min),ganttIso(max))+1)};
  let conflictCount=0; const risks=[]; deps.forEach(d=>{ const pred=taskById(d.predecessorId), succ=taskById(d.successorId); if(!pred||!succ) return; const req=ganttAddDays(taskEndDate(pred), Number(d.lagDays||0)); const actual=succ.start||succ.due; if(ganttDate(actual)<ganttDate(req)&&succ.status!=='DONE'){ conflictCount++; risks.push({level:d.critical?'high':'medium', taskId:succ.id, title:`Dependency conflict: ${succ.name} starts before ${pred.name} finishes`, recommendation:`Move ${succ.name} to ${req} or reduce predecessor duration.`}); }});
  tasks.forEach(t=>{ if(t.status==='BLOCKED' && criticalPath.includes(t.id)) risks.push({level:'high', taskId:t.id, title:`Critical path task is blocked: ${t.name}`, recommendation:'Escalate blocker and run schedule cascade.'}); if(t.status!=='DONE' && t.due && ganttDate(t.due)<ganttDate(new Date())) risks.push({level:'high', taskId:t.id, title:`Overdue task threatens schedule: ${t.name}`, recommendation:'Reschedule or assign recovery work.'}); });
  const viewTasks=tasks.map(t=>{ const start=t.start||t.due; const end=taskEndDate(t); return {...t, start, end, criticalPath:criticalPath.includes(t.id), critical:t.critical || criticalPath.includes(t.id), predecessors:deps.filter(d=>d.successorId===t.id).map(d=>d.predecessorId), successors:deps.filter(d=>d.predecessorId===t.id).map(d=>d.successorId), offsetDays:Math.max(0,ganttDayDiff(timeline.start,start)), widthDays:Math.max(1,ganttDayDiff(start,end)), timelineDays:timeline.days}; });
  return {ok:true, projectId, timeline, tasks:viewTasks, dependencies:deps, criticalPath, risks, metrics:{taskCount:tasks.length, dependencyCount:deps.length, criticalTasks:criticalPath.length, riskCount:risks.length, conflictCount, endDate:timeline.end, blockedCritical:tasks.filter(t=>t.status==='BLOCKED'&&criticalPath.includes(t.id)).length}};
}
function ganttMetricCard(label,value,trend){ return `<div class="gantt-metric"><span>${escapeHtml(label)}</span><b>${value}</b><em>${escapeHtml(trend)}</em></div>`; }
function renderGanttTaskRow(t,timeline){ const left=(t.offsetDays/Math.max(1,timeline.days))*100; const width=Math.max(5,(t.widthDays/Math.max(1,timeline.days))*100); const member=memberById(t.assignee||'adrian'); const cls=t.criticalPath?'critical':(t.blocked?'blocked':''); return `<div class="gantt-task-row ${cls}"><div class="gantt-task-name" onclick="openTask('${t.id}')"><b>${escapeHtml(t.name)}</b><span><span class="avatar tiny ${member.avatar}">${member.initials}</span> ${escapeHtml(member.name)} • ${t.status}</span></div><div class="gantt-track"><div class="gantt-dep-line">${(t.predecessors||[]).length?'↤ '+t.predecessors.length+' pred':''}</div><div class="gantt-bar-v7 ${cls}" style="left:${left}%;width:${width}%"><span>${t.progress||0}%</span></div></div><div class="gantt-row-actions"><input type="date" value="${t.start||''}" onchange="rescheduleGanttTask('${t.id}', this.value, null, true)"/><input type="number" min="1" value="${t.duration||1}" onchange="rescheduleGanttTask('${t.id}', null, Number(this.value), true)"/><button class="btn-secondary btn-small" onclick="shiftGanttTask('${t.id}',1)">＋1d</button></div></div>`; }
function renderDependencyRow(d){ const pred=taskById(d.predecessorId), succ=taskById(d.successorId); return `<div class="dependency-row"><div><b>${escapeHtml(pred?.name||d.predecessorId)}</b><span>→ ${escapeHtml(succ?.name||d.successorId)} • ${d.type||'FS'} +${d.lagDays||0}d ${d.critical?'• critical':''}</span></div><button class="btn-secondary btn-small" onclick="removeGanttDependency('${d.id}')">Remove</button></div>`; }
function applyGanttPayload(data){ if(!data) return; if(data.state){ state={...state,...data.state}; ensureGanttState(); } if(data.dependencies) state.taskDependencies=data.dependencies; if(data.baselines) state.ganttBaselines=data.baselines; if(data.risks) state.ganttRiskAlerts=data.risks; if(data.metrics) state.ganttMetrics=data.metrics; lastGanttDataset=data; ganttStatusText=apiOnline?'API Gantt synced':'Local Gantt'; }
async function refreshGanttFromApi(showToast=true){ ensureGanttState(); if(!apiOnline){ lastGanttDataset=computeLocalGanttDataset(state.selectedProject); if(showToast) toast('Gantt running locally'); render(); return; } try{ const res=await fetch(`${API_BASE}/gantt?project_id=${state.selectedProject}`, {headers:authHeaders(), cache:'no-store'}); if(!res.ok) throw new Error('Gantt API failed'); const data=await res.json(); applyGanttPayload(data); saveState(); if(showToast) toast('Gantt refreshed from API'); render(); }catch(err){ console.warn(err); apiOnline=false; lastGanttDataset=computeLocalGanttDataset(state.selectedProject); if(showToast) toast('Gantt API unavailable; using local engine'); render(); }}
async function recalculateGantt(){ if(apiOnline){ try{ const res=await fetch(`${API_BASE}/gantt/recalculate?project_id=${state.selectedProject}`, {method:'POST', headers:authHeaders()}); if(res.ok){ const data=await res.json(); applyGanttPayload(data); toast(`Critical path: ${data.metrics?.criticalTasks||0} tasks • ${data.metrics?.riskCount||0} risks`); saveState(); render(); return; }}catch(err){ console.warn(err); }} lastGanttDataset=computeLocalGanttDataset(state.selectedProject); toast(`Local critical path: ${lastGanttDataset.metrics.criticalTasks} tasks • ${lastGanttDataset.metrics.riskCount} risks`); saveState(); render(); }
async function addGanttDependencyFromControls(){ const pred=$('#ganttPred')?.value; const succ=$('#ganttSucc')?.value; const lag=Number($('#ganttLag')?.value||0); if(!pred||!succ||pred===succ){ toast('Choose two different tasks'); return; } if(apiOnline){ try{ const res=await fetch(`${API_BASE}/gantt/dependencies`, {method:'POST', headers:{'Content-Type':'application/json', ...authHeaders()}, body:JSON.stringify({predecessor_task_id:pred, successor_task_id:succ, dependency_type:'FS', lag_days:lag, critical:false})}); if(res.ok){ const data=await res.json(); applyGanttPayload(data); toast('Dependency linked'); saveState(); render(); return; } const err=await res.json().catch(()=>({detail:'Could not link'})); toast(err.detail||'Dependency not linked'); return; }catch(e){ console.warn(e); }} state.taskDependencies.push({id:uid(), predecessorId:pred, successorId:succ, type:'FS', lagDays:lag, critical:false}); lastGanttDataset=computeLocalGanttDataset(state.selectedProject); toast('Dependency linked locally'); saveState(); render(); }
async function removeGanttDependency(id){ if(apiOnline){ try{ const res=await fetch(`${API_BASE}/gantt/dependencies/${id}`, {method:'DELETE', headers:authHeaders()}); if(res.ok){ const data=await res.json(); applyGanttPayload(data); toast('Dependency removed'); saveState(); render(); return; }}catch(e){ console.warn(e); }} state.taskDependencies=(state.taskDependencies||[]).filter(d=>d.id!==id); lastGanttDataset=computeLocalGanttDataset(state.selectedProject); toast('Dependency removed locally'); saveState(); render(); }
async function rescheduleGanttTask(taskId, start, duration, cascade=true){ const t=taskById(taskId); if(!t) return; const newStart=start || t.start || t.due; const newDuration=duration || Number(t.duration||1); if(apiOnline){ try{ const res=await fetch(`${API_BASE}/gantt/tasks/${taskId}/schedule`, {method:'POST', headers:{'Content-Type':'application/json', ...authHeaders()}, body:JSON.stringify({start:newStart, duration:newDuration, cascade, reason:'Updated from Gantt row controls'})}); if(res.ok){ const data=await res.json(); applyGanttPayload(data); toast(`Task rescheduled${cascade?' and dependents checked':''}`); saveState(); render(); return; }}catch(e){ console.warn(e); }} t.start=newStart; t.duration=newDuration; t.due=ganttAddDays(newStart,newDuration); if(cascade) cascadeLocalFrom(taskId); lastGanttDataset=computeLocalGanttDataset(state.selectedProject); toast('Task rescheduled locally'); saveState(); render(); }
function shiftGanttTask(taskId, days){ const t=taskById(taskId); if(!t) return; rescheduleGanttTask(taskId, ganttAddDays(t.start||t.due, days), null, true); }
function cascadeLocalFrom(taskId, seen=new Set()){ if(seen.has(taskId)) return; seen.add(taskId); const pred=taskById(taskId); if(!pred) return; (state.taskDependencies||[]).filter(d=>d.predecessorId===taskId).forEach(d=>{ const succ=taskById(d.successorId); if(!succ) return; const required=ganttAddDays(taskEndDate(pred), Number(d.lagDays||0)); if(ganttDate(succ.start||succ.due)<ganttDate(required)){ succ.start=required; succ.due=ganttAddDays(required, Math.max(1,Number(succ.duration||1))); cascadeLocalFrom(succ.id, seen); }}); }
async function createGanttBaseline(){ const name=prompt('Baseline name', `Baseline ${new Date().toLocaleDateString()}`); if(!name) return; if(apiOnline){ try{ const res=await fetch(`${API_BASE}/gantt/baselines`, {method:'POST', headers:{'Content-Type':'application/json', ...authHeaders()}, body:JSON.stringify({project_id:state.selectedProject, name})}); if(res.ok){ const data=await res.json(); applyGanttPayload(data); toast('Baseline captured'); saveState(); render(); return; }}catch(e){ console.warn(e); }} const snapshots=projectTasks().map(t=>({taskId:t.id,name:t.name,start:t.start,due:t.due,duration:t.duration,status:t.status,progress:t.progress})); state.ganttBaselines.push({id:uid(), projectId:state.selectedProject, name, taskSnapshots:snapshots, createdAt:new Date().toISOString()}); toast('Baseline captured locally'); saveState(); render(); }

window.refreshPlannerFromApi = refreshPlannerFromApi;
window.setPlannerDate = setPlannerDate;
window.shiftPlannerDate = shiftPlannerDate;
window.quickScheduleTask = quickScheduleTask;
window.addFocusBlock = addFocusBlock;
window.removePlannerBlock = removePlannerBlock;
window.clearAISchedule = clearAISchedule;
window.addCalendarMeetingDemo = addCalendarMeetingDemo;
window.aiTaskSummary = aiTaskSummary;
window.aiCreateSubtasks = aiCreateSubtasks;
window.globalSearch = globalSearch;
window.resetDemoData = resetDemoData;
window.showDataLayerStatus = showDataLayerStatus;
window.syncStateToApi = syncStateToApi;
window.ensureDemoAuth = ensureDemoAuth;
window.dismissBanner = dismissBanner;


window.setVisualTab = setVisualTab;
window.selectWhiteboard = selectWhiteboard;
window.createWhiteboard = createWhiteboard;
window.addSticky = addSticky;
window.addCanvasCard = addCanvasCard;
window.convertStickyToTask = convertStickyToTask;
window.linkObjectToTask = linkObjectToTask;
window.runWhiteboardAI = runWhiteboardAI;
window.refreshWhiteboardsFromApi = refreshWhiteboardsFromApi;
window.selectVisualObject = selectVisualObject;
window.openCanvasLink = openCanvasLink;

render();
hydrateFromApi();

window.refreshGanttFromApi = refreshGanttFromApi;
window.recalculateGantt = recalculateGantt;
window.addGanttDependencyFromControls = addGanttDependencyFromControls;
window.removeGanttDependency = removeGanttDependency;
window.rescheduleGanttTask = rescheduleGanttTask;
window.shiftGanttTask = shiftGanttTask;
window.createGanttBaseline = createGanttBaseline;
