"""Student workflow for offline planning, matched navigation and social trials."""
import json
import shutil
import time
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from evaluation.experiments import offline_checks, navigation_checks, social_checks
from lab.storage import ROOT, submission_root, atomic_json, load, save, sha, save_evidence, export
from planning.core import make_map, inflate, START, GOAL, cell_to_world, reference_path, fingerprint, EXPERIMENT_VERSION
from planning.experiments import run_offline
from planning.social import PEOPLE, CONFIGS, refine

STAGES = ['intro','concepts','preflight','mission_1','mission_2','mission_3','final']
LABELS = ['Welcome','Planning playground','Environment check','Mission 1: Implement searches',
          'Mission 2: Navigate two maps','Mission 3: Navigate around people','Synthesis and submission']


def ensure_planner_source():
    """Create the editable starter on first launch, never overwrite student code."""
    source = submission_root()/'mission_1/planners.py'
    source.parent.mkdir(parents=True,exist_ok=True)
    if not source.exists():
        starter = (Path(__file__).resolve().parents[1]/'student_planners.py').read_text(encoding='utf-8')
        with source.open('x',encoding='utf-8') as output:
            output.write(starter)
    return source


def response(st,key,label):
    widget = 'answer.'+key
    if widget not in st.session_state:
        st.session_state[widget] = st.session_state['responses'].get(key,'')
    value = st.text_area(label,key=widget,height=130)
    st.session_state['responses'][key] = value
    return bool(value.strip())


def map_plot(st,name='open',paths=None,people=(),checkpoint=None):
    fig,ax = plt.subplots(figsize=(7,4))
    ax.imshow(make_map(name,people),origin='lower',extent=(-5,5,-4,4),cmap='Greys',vmin=0,vmax=1)
    for label,points in (paths or {}).items():
        if points:
            ax.plot(*zip(*points),label=label,linewidth=1.5,linestyle='--' if '(partial)' in label else '-')
    for cell,color,label in ((START,'green','Start'),(GOAL,'red','Goal')):
        x,y = cell_to_world(cell)
        ax.scatter([x],[y],c=color,s=40)
        ax.annotate(label,(x,y),xytext=(4,5),textcoords='offset points',fontsize=8)
    from matplotlib.patches import Circle
    if checkpoint is not None:
        ax.scatter([checkpoint['x']],[checkpoint['y']],marker='o',s=100,facecolors='none',edgecolors='#ca2380',linewidths=2,label='Inspected position')
    for p in people:
        ax.add_patch(Circle((p['x'],p['y']),p['radius'],color='orange'))
        ax.add_patch(Circle((p['x'],p['y']),p['radius']+.18+.75,fill=False,color='orange',linestyle=':'))
    ax.set(xlabel='x (m)',ylabel='y (m)',title=name.capitalize()+' map',aspect='equal')
    if paths:
        ax.legend(loc='upper left',fontsize=7)
    fig.tight_layout()
    st.pyplot(fig,width=700)
    plt.close(fig)


def checks_table(st,checks):
    st.dataframe(pd.DataFrame([{'Requirement':label,'Status':'Ready' if ready else 'Not ready'} for label,ready in checks]),hide_index=True,width='stretch')
    return all(ready for _,ready in checks)


def finish(st,mission,evidence,checks,answers):
    ready = checks_table(st,checks)
    if not answers:
        st.info('Complete the analysis responses before saving this mission.')
    if st.button('Check and save '+mission.replace('_',' ').title(),disabled=not(ready and answers),type='primary'):
        st.session_state['evidence'][mission] = evidence
        save_evidence(mission,evidence,st.session_state['responses'])
        write_reports(mission,evidence)
        if mission not in st.session_state['completed_missions']:
            st.session_state['completed_missions'].append(mission)
        save(st.session_state)
        st.success('Mission saved. Continue using the button at the bottom of this page.')


def write_reports(mission,evidence):
    """Keep CSV and plotted evidence in the submission, not just in downloads."""
    rows = evidence.get('rows',[])
    folder = submission_root()/mission
    folder.mkdir(parents=True,exist_ok=True)
    scalars = [{k:v for k,v in r.items() if not isinstance(v,(list,dict)) and k!='_file'} for r in rows]
    frame = pd.DataFrame(scalars)
    frame.to_csv(folder/'metrics.csv',index=False)
    if rows and mission!='mission_1':
        frame['success'] = frame['status'].eq('succeeded').astype(float)
        groups = frame.groupby(['map','planner','condition'])
        summary = groups.agg(attempts=('status','size'),success_rate=('success','mean'))
        summary.to_csv(folder/'outcomes.csv')
    for name in ('open','constrained'):
        relevant = [r for r in rows if r.get('map')==name]
        if not relevant:
            continue
        for condition in sorted({r.get('condition','offline') for r in relevant}):
            fig,ax = plt.subplots(figsize=(8,5))
            selected = [r for r in relevant if r.get('condition','offline')==condition]
            people = selected[0].get('people',())
            ax.imshow(make_map(name,people),origin='lower',extent=(-5,5,-4,4),cmap='Greys',vmin=0,vmax=1)
            for row in selected:
                points = row.get('path',[]) if mission=='mission_1' else [(s['x'],s['y']) for s in row.get('trajectory',[])]
                if mission=='mission_1':
                    points = [cell_to_world(p) for p in points]
                if points:
                    ax.plot(*zip(*points),label=row['planner']+' '+row['status'],linewidth=1)
            ax.set(xlabel='x (m)',ylabel='y (m)',title=f'{name}: {condition}',aspect='equal')
            handles,labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(fontsize=7)
            fig.tight_layout()
            fig.savefig(folder/f'{name}_{condition}.png',dpi=120)
            plt.close(fig)


def intro(st):
    st.title('Lab 8: Planning and Human-Aware Navigation')
    st.write('How does a path become successful robot navigation? First implement four search algorithms on grids. '
             'Then execute their paths, supplied sampling-based paths and a Nav2 path in two matching simulated environments. '
             'Finally investigate whether a robot that avoids physical contact also moves considerately around people.')
    st.markdown('''1. **Mission 1, offline Python:** implement BFS, DFS, IDDFS and A*. Compare search work and path quality.
2. **Mission 2, ROS 2 simulation:** compare seven planners on an open map and a constrained map using one controller.
3. **Mission 3, social navigation:** compare human-unaware paths and two potential-field configurations for at least two planners.''')
    st.write('A planner chooses a route. A controller tries to follow it using pose and sensor evidence. A short planned path can still '
             'be difficult to execute. A collision-free route can still pass uncomfortably close to a person.')
    st.info('Write real Python search code in Mission 1. Map handling, collision checks, metrics, RRT, PRM and robot trial tools are supplied. '
            'Work individually and keep unsuccessful attempts as evidence.')
    st.write('The app and ROS desktop must use the same course repository folder. Work is saved locally as you progress. '
             'You can revisit pages. Your name and student ID or email are collected at submission time.')
    st.caption(f'Submission folder: {submission_root()}')
    st.subheader('Where your code fits')
    from lab.planning_playground import architecture
    architecture(st)


def concepts(st):
    from lab.planning_playground import render
    render(st)


def preflight(st):
    st.header('Check the experiment environment')
    st.write('Mission 1 needs Python, not ROS. Missions 2 and 3 need the course ROS 2 desktop. Build the supplied package once. '
             'Run the following in a terminal inside that desktop, not in host PowerShell.')
    st.code('cd /workspace/week09_planning_navigation\nsource /opt/ros/jazzy/setup.bash\ncd ros2_ws\ncolcon build --symlink-install\ncd ..\nbash scripts/course_preflight.sh',language='bash')
    st.write('The check verifies ROS 2 Jazzy, Gazebo, Nav2, TurtleBot3, the built experiment package and the common ROS domain. '
             'It writes its report into this repository. It does not claim that a simulation is already running. Each trial separately '
             'checks Nav2 actions, transforms and live lidar before moving.')
    reference_path(inflate(make_map('open')))
    st.success('Offline planning tools and canonical maps are available.')
    path = ROOT/'runtime/preflight.json'
    if path.exists():
        try:
            report = json.loads(path.read_text())
            st.dataframe(pd.DataFrame([{'Check':k,'Passed':v} for k,v in report['checks'].items()]),hide_index=True)
            st.caption('Checked '+time.ctime(report['checked_unix']))
        except (ValueError,KeyError):
            st.warning('The saved environment report is unreadable. Rerun the check.')
    else:
        st.info('No ROS environment report found yet. You can complete Mission 1 before starting ROS.')
    st.write('Use run_trials.sh for robot experiments. It uses ROS_DOMAIN_ID=29 and a private Gazebo transport partition for each attempt. '
             'Do not run another Lab 8 simulation alongside a batch.')
    st.button('Refresh environment report')


def mission1(st):
    st.header('Mission 1: Implement and compare four searches')
    st.write('Write the route-finding logic for BFS, DFS, IDDFS and A*. Each receives the same inflated grid, start, goal, neighbour '
             'order and measurement interface. No robot is launched in this mission.')
    source = ensure_planner_source()
    st.subheader('1. Open your Python file')
    st.write('Open the following file in VS Code or another editor. The starter file is already provided. Replace the four '
             'NotImplementedError statements with your implementations and save in your editor. The checks below always read the saved file.')
    st.code(str(source),language=None)
    st.caption('When editing on your host computer, open week09_planning_navigation/student_submission/mission_1/planners.py '
               'inside your course repository. The /workspace path above is the same shared file as seen inside Docker.')
    st.info('You may use AI to help implement the planners. You remain responsible for testing the code and explaining what '
            'you implemented, how it works, and how the four search methods differ. Do not replace your implementation with the reference planner.')
    st.subheader('2. Understand the graph and ctx')
    st.markdown('#### First, the intuition: a problem packet, not a planner')
    st.write('Imagine someone handing you a paper maze, marking the start and destination, and giving you a tool that '
             'lists the legal exits from any square. You still decide which square to investigate next and remember how you got there. '
             'ctx is that packet of information and tools. It saves you from writing the map-loading and measurement code '
             'so you can concentrate on the search. It is not the robot, the current cell, or an algorithm that finds the route for you.')
    from lab.planning_visuals import context_handoff_figure,context_example_figure,context_example,show_figure
    show_figure(st,context_handoff_figure())
    st.caption('The runner hands the same kind of packet to each method, with a fresh set of counters for each test. '
               'Your code supplies the search decisions and returns the route.')
    st.markdown('#### More technically: a Python object passed into your function')
    st.write('ctx is a variable name, short for context. Its value is an instance of the supplied SearchContext class. '
             'The runner creates that object and calls your function, for example bfs(ctx). You do not need to create it yourself. '
             'A dot accesses something in that object: ctx.start reads stored data, while ctx.expand(...) calls one of its methods. '
             'Each planner receives the map, endpoints, and tools through this one argument instead of many separate arguments.')
    st.write('There is no separate graph object. The graph is implicit in a rectangular list of lists called ctx.grid. '
             'Each free cell is a vertex, represented by a (row, column) tuple. An edge connects it to a free cell one step '
             'up, down, left, or right. Each edge costs 1. A wall is 1 and free space is 0. Row zero is at the bottom. '
             'Mission maps already include obstacle inflation for a 0.18 m robot planning radius. Do not inflate them again.')
    st.table(pd.DataFrame([
        ['ctx.start, ctx.goal','Starting and destination cell tuples'],
        ['ctx.grid','Read-only occupancy grid for this test'],
        ['ctx.expand(cell, frontier_size)','Returns legal next cells in right, up, left, down order and counts one expansion'],
        ['ctx.heuristic(cell)','Manhattan distance to the goal, an estimate that ignores walls'],
        ['reconstruct(parent, goal)','Returns the ordered route from a parent dictionary']
    ],columns=['Interface','Meaning']))
    st.markdown('#### A concrete example: ask about one cell')
    example,current,adjacent = context_example()
    left,right = st.columns(2)
    with left:
        show_figure(st,context_example_figure(),width=480)
        st.caption('S and G are the endpoints. The red outline marks current. Gold outlines and arrows show the legal next cells. '
                   'There is no arrow into the wall on the right.')
    with right:
        st.code(f'ctx.start          # {example.start}\nctx.goal           # {example.goal}\ncurrent = {current}\n\nnext_cells = ctx.expand(current, 5)\n# returns {adjacent}\n\nctx.heuristic(current)  # {example.heuristic(current)}\nctx.expanded            # {example.expanded} after this call',language='python')
        st.write('Calling expand asks which moves are legal and records one expansion. It does not choose a neighbor, '
                 'move a robot, or update your frontier. The heuristic returns 3 because the goal is three columns away. '
                 'The real route must go around the wall, so 3 is only a lower-bound estimate, not a route length.')
        st.write('The argument 5 assumes four other candidates are waiting, plus the current cell. It records frontier size '
                 'for the memory comparison. It does not ask for five neighbors or change which moves are legal.')
    st.markdown('#### What your implementation does with ctx')
    st.markdown('''1. Read `ctx.start` and `ctx.goal`, then create your own frontier, visited or cost records, and parent links.
2. Remove the next cell from your queue, stack, or heap. Your algorithm chooses this order, not `ctx`.
3. If that cell is the goal, return the route. Otherwise call `ctx.expand` once to get its legal next cells.
4. Decide which returned cells to add or improve. Update your own frontier and parents. A* also calls `ctx.heuristic` for priorities.
5. Keep using the same `ctx` for the whole test, including every IDDFS depth limit. Return a cell list or `[]`, not the context object.''')
    st.code('for nxt in ctx.expand(current, len(frontier) + 1):\n    # nxt is a legal (row, column) neighbor\n    ...',language='python')
    st.caption('Call expand once for each cell whose successors you examine, including repeated IDDFS work. '
               'The +1 includes the current cell just removed from the frontier. Do not catch its budget exception.')
    st.subheader('3. Choose the next candidate: queue, stack, or heap')
    st.write('The frontier stores cells waiting to be examined. A queue removes the oldest entry, like a line at a store. '
             'BFS uses this first-in, first-out order. A stack removes the newest entry, like the top plate on a pile. '
             'DFS uses this last-in, first-out order. A heap is a priority queue that removes the entry with the smallest numeric priority. '
             'A* uses priority g + h, where g is the cost so far and h is ctx.heuristic(cell).')
    st.code('from collections import deque\nfrom heapq import heappush, heappop\nfrom planning.core import reconstruct\n\nqueue = deque([ctx.start])\ncurrent = queue.popleft()  # BFS removes the oldest entry\nstack = [ctx.start]\ncurrent = stack.pop()     # DFS removes the newest entry\nheap = []\nheappush(heap, (priority, cost_so_far, cell))\npriority, cost_so_far, current = heappop(heap)',language='python')
    st.write('deque comes from Python collections and supports efficient removal from the front. heappush and heappop '
             'come from Python heapq and maintain minimum-priority order. reconstruct is a supplied course helper, not a search algorithm. '
             'These imports are already in your starter file. The snippets explain data structures, not complete planners.')
    st.subheader('4. Record discoveries and build the route')
    st.write('Store parent = {ctx.start: None}. When you first reach nxt from current, record parent[nxt] = current. '
             'For BFS, mark discovery when adding a cell to the queue so it is not queued repeatedly. DFS also needs cycle prevention. '
             'For A*, store the best g cost for each cell, update its parent if a cheaper route is found, and skip stale heap entries. '
             'When the goal is selected, return reconstruct(parent, ctx.goal), including both endpoints.')
    st.subheader('5. Add iterative deepening and handle failure')
    st.write('IDDFS repeats a depth-limited DFS with limits 0, 1, 2, and so on. Each pass starts fresh. Prevent cycles on '
             'the current path rather than keeping a visited set across limits. A depth cutoff is not exhaustive failure. '
             'If a free start equals the goal, return [ctx.start]. If either endpoint is a wall, return []. '
             'Otherwise return [] only when search is exhausted. A resource limit means the runner stopped work, not that no path exists.')
    st.caption('Optional helper: planning.core.free(grid, cell) checks bounds and occupancy. '
               'No additional graph package is needed. Use only Python standard-library data structures.')
    small_checks(st,source)
    st.subheader('7. Evaluate fixed conditions')
    st.write('Run all methods on a short diagnostic corridor, open and constrained maps, and an unreachable-goal case. '
             'The corridor lets you verify all algorithms, including IDDFS, before larger searches. Open and constrained maps are reused in Mission 2. The unreachable '
             'case is a small pair of chambers separated by an unbroken wall. S and G are both free, but no legal sequence of moves connects them. '
             'This case is deliberately small so a correct search, including IDDFS, can exhaust the reachable chamber and return no_path. '
             'Each search has a 250,000 expansion budget and a 12 second worker limit. IDDFS on larger reachable maps may reach '
             'a resource limit. A timeout does not mean no path exists. Successful planning times exclude process startup and rendering.')
    if st.button('Evaluate all four planners',disabled=not source.exists()):
        with st.spinner('Running isolated search workers'):
            evidence = run_offline(source)
            st.session_state['evidence']['offline_draft'] = evidence
            atomic_json(submission_root()/'mission_1/offline_results.json',evidence)
    evidence = st.session_state['evidence'].get('offline_draft',st.session_state['evidence'].get('mission_1',{}))
    rows = evidence.get('rows',[])
    if rows:
        from planning.experiments import cases
        expected_maps = {name:fingerprint(grid) for name,(grid,_,_) in cases().items()}
        if any(r.get('map_hash')!=expected_maps.get(r.get('map')) for r in rows):
            st.warning('The test maps have changed since these results were saved. Select Evaluate all four planners again. '
                       'Earlier results are kept, but cannot complete the revised mission.')
        frame = pd.DataFrame(rows).reindex(columns=['map','planner','status','planning_s','expanded','peak_frontier','path_length_m','optimal_length_m','optimality_ratio','error'])
        st.dataframe(frame,hide_index=True,width='stretch')
        st.download_button('Download search metrics CSV',frame.to_csv(index=False),'search_metrics.csv','text/csv')
        st.subheader('Inspect all four test maps')
        from lab.planning_playground import show_grid
        for pair in (('diagnostic','open'),('constrained','unreachable')):
            for column,name in zip(st.columns(2),pair):
                with column:
                    if name in ('open','constrained'):
                        map_plot(st,name,{r['planner']:[cell_to_world(p) for p in r.get('path',[])] for r in rows if r['map']==name and r['status']=='succeeded'})
                    else:
                        from planning.experiments import cases
                        # These are the same cases passed to the workers.
                        grid,start,goal = cases()[name]
                        fig = __import__('lab.planning_playground',fromlist=['grid_figure']).grid_figure(grid,start,goal,name)
                        ax = fig.axes[0]
                        for row in rows:
                            if row['map']==name and row.get('path') and row.get('map_hash')==fingerprint(grid):
                                ax.plot([p[1] for p in row['path']],[p[0] for p in row['path']],label=row['planner'])
                        if ax.get_legend_handles_labels()[0]: ax.legend(fontsize=7)
                        st.pyplot(fig,width=620)
                        plt.close(fig)
                        if name=='unreachable':
                            st.caption('The full-height dividing wall disconnects two free endpoints. There is no feasible path. '
                                       'A resource_limit result describes an unfinished search, not the reason this map is disconnected.')
        st.write('invalid_path violates the grid or endpoints. missed_path returned no path when one exists. implementation_error '
                 'includes incomplete functions and Python exceptions. Fix these. resource_limit records an implemented search that '
                 'ran out of work or time. no_path is checked against the reference search.')
    st.subheader('8. Interpret the comparison')
    st.info('BFS and A* should have the same shortest path length on these unit-cost grids. A* uses its heuristic to guide '
            'which cells it examines, not to improve on the shortest possible route. Compare expanded nodes and planning time to see its search benefit.')
    a = response(st,'mission_1.search','On the open map, copy the BFS and A* path lengths and expanded-node counts from the table. '
                 'Are the lengths equal? Which examined fewer cells? Explain how the queue and heuristic produce this result, referring to your code.')
    b = response(st,'mission_1.failure','Compare your DFS and IDDFS rows with BFS on the constrained map. Name one difference in '
                 'path length, expansions, or status and explain it using your implementations. Then report the four unreachable-case statuses. '
                 'Explain the difference between no_path and resource_limit. Mention any AI help and what you checked yourself.')
    checks = offline_checks(evidence)+[('Results match saved source',source.exists() and evidence.get('source_sha256')==sha(source))]
    finish(st,'mission_1',evidence,checks,a and b)


def small_checks(st,source):
    from planning.teaching import small_cases
    from planning.experiments import student_search
    from lab.planning_playground import show_grid
    st.subheader('6. Check one small case before the full evaluation')
    st.write('Select a saved implementation and one small test. Start with start equals goal and the empty grid, then '
             'try a detour, an occupied goal, a disconnected goal and a narrow passage. These checks are debugging aids, '
             'not another assignment or extra written responses. A small-case success does not replace the full evaluation below.')
    method = st.selectbox('Implementation to check',['bfs','dfs','iddfs','astar'],key='small_check_method',format_func=str.upper)
    cases = small_cases()
    name = st.selectbox('Small test case',list(cases),key='small_check_case')
    case = cases[name]
    st.write(case['note'])
    show_grid(st,case['grid'],case['start'],case['goal'],name)
    if st.button('Run selected check',disabled=not source.exists(),key='run_small_check'):
        with st.spinner('Checking your saved Python function'):
            row = student_search(source,method,case['grid'],case['start'],case['goal'])
        row.update(case=name,planner=method,source_sha256=sha(source))
        expected = reference_path(case['grid'],case['start'],case['goal'])
        row['expected_status'] = 'succeeded' if expected else 'no_path'
        row['check_passed'] = row['status']==row['expected_status'] and (method not in ('bfs','astar','iddfs') or
            not expected or row.get('optimality_ratio')==1)
        st.session_state['evidence']['small_check'] = row
        atomic_json(submission_root()/'mission_1/latest_small_check.json',row)
    row = st.session_state['evidence'].get('small_check',{})
    if row and row.get('case')==name and row.get('planner')==method:
        if not source.exists() or row.get('source_sha256')!=sha(source):
            st.info('Your source has changed. Run this check again.')
        else:
            (st.success if row['check_passed'] else st.warning)(f"Expected: {row['expected_status']}. Your result: {row['status']}.")
            if row.get('error'):
                st.error(row['error'])
            st.dataframe(pd.DataFrame([{k:row.get(k) for k in ('status','expanded','peak_frontier','path_length_m','optimality_ratio')}]),hide_index=True)
            if row.get('path'):
                show_grid(st,case['grid'],case['start'],case['goal'],'Your returned path',frame={'path':row['path']})


def read_trials(mission):
    latest = {}
    for path in (ROOT/'runtime/trials').glob('*/result.json'):
        try:
            row = json.loads(path.read_text())
            if row.get('schema')!=2 or row.get('experiment_version')!=EXPERIMENT_VERSION or str(row.get('mission'))!=str(mission):
                continue
            row['_file'] = str(path)
            key = (row['map'],row['planner'],row['seed'],row['condition'])
            if key not in latest or path.stat().st_mtime>Path(latest[key]['_file']).stat().st_mtime:
                latest[key] = row
        except (OSError,ValueError,KeyError):
            continue
    return list(latest.values())


def trial_table(st,mission):
    rows = read_trials(mission)
    if not rows:
        st.info('No trials found yet. Run the terminal command, then refresh this page.')
        return []
    columns = ['run_id','map','planner','seed','condition','status','planning_s','elapsed_s','distance_m','planned_length_m',
               'goal_error_m','mean_tracking_error_m','minimum_static_clearance_m','minimum_lidar_range_m','minimum_person_clearance_m','personal_space_s','max_speed_near_people_mps','field_status','planner_error_code','controller_error_code','error']
    frame = pd.DataFrame([{k:v for k,v in r.items() if k in columns} for r in rows])
    st.dataframe(frame,hide_index=True,width='stretch')
    st.download_button('Download trial metrics CSV',frame.to_csv(index=False),f'mission_{mission}_metrics.csv','text/csv')
    st.caption('Latest attempt per map, planner, repeat and condition. Earlier attempts and logs remain in runtime/trials.')
    metrics = [m for m in ['elapsed_s','distance_m','planning_s','personal_space_s','minimum_person_clearance_m'] if m in frame and frame[m].notna().any()]
    if metrics:
        metric = st.selectbox('Compare metric',metrics,key=f'metric{mission}')
        success_only = st.checkbox('Plot successful trials only',value=True,key=f'success_only{mission}')
        st.write('Bars average recorded numeric outcomes in the selected subset. Failures without measurements are not zeros. '
                 'Use the outcome summary below to include failures when assessing reliability.')
        plotted = frame[frame['status']=='succeeded'] if success_only else frame
        if not plotted.dropna(subset=[metric]).empty:
            chart = plotted.dropna(subset=[metric]).groupby(['map','planner','condition'])[metric].mean().reset_index()
            for column,name in zip(st.columns(2),('open','constrained')):
                with column:
                    st.write('**'+name.capitalize()+' map**')
                    subset = chart[chart['map']==name].copy()
                    subset['Trial'] = subset['planner']+' / '+subset['condition']
                    if subset.empty:
                        st.info('No measured results for this map in the selected subset.')
                    else:
                        st.bar_chart(subset.set_index('Trial')[[metric]])
        else:
            st.info('No measured values in this subset. Inspect statuses or include unsuccessful attempts.')
    frame['success'] = frame['status'].eq('succeeded').astype(float)
    st.write('Outcome summary: attempts include resource limits and execution failures, but environment failures need rerunning. '
             'A success rate of 1 from a single attempt means one observed success, not proven reliability.')
    st.dataframe(frame.groupby(['map','planner','condition']).agg(attempts=('status','size'),success_rate=('success','mean')),width='stretch')
    chosen = st.selectbox('Inspect an attempt',range(len(rows)),format_func=lambda i:rows[i]['run_id'],key=f'inspect{mission}')
    row = rows[chosen]
    if row.get('planning_metrics'):
        with st.expander('Planning details for this attempt'):
            st.write('Sampling planners report sampled nodes and collision checks, which are not directly equivalent to grid expansions. '
                     'PRM includes roadmap construction time (build_s) as well as graph-query time (query_s). Total planning_s includes both.')
            st.json(row['planning_metrics'])
    paths = {'Planned':row.get('path',[])}
    if row.get('trajectory'):
        paths['Executed estimate'] = [(s['x'],s['y']) for s in row['trajectory']]
    map_plot(st,row['map'],paths,row.get('people',()))
    if row.get('error'):
        st.error(row['error'])
    st.caption(f"Attempt logs: {Path(row['_file']).parent}")
    return rows


def copy_trials(rows,mission):
    for row in rows:
        folder = submission_root()/mission/'trials'/row['run_id']
        folder.mkdir(parents=True,exist_ok=True)
        for filename in ('result.json','request.json','map.yaml','map.pgm','nav2.yaml','planners.py','launch.log','probe.log'):
            source = Path(row['_file']).parent/filename
            if source.exists():
                shutil.copy2(source,folder/filename)


def trial_files_ready(mission,rows):
    for row in rows:
        folder = submission_root()/mission/'trials'/row['run_id']
        if not (folder/'result.json').exists() or not (folder/'request.json').exists():
            return False
        if row.get('trajectory') and not (folder/'nav2.yaml').exists():
            return False
    return bool(rows)


def inspect_navigation(st,rows):
    """Student scrubs a real trajectory and retains an identified checkpoint."""
    available = [r for r in rows if r.get('trajectory')]
    if not available:
        st.info('Run a moving trial first to inspect a recorded trajectory.')
        return False
    index = st.selectbox('Choose a trajectory to investigate',range(len(available)),
        format_func=lambda i:available[i]['run_id'],key='audit_run')
    row = available[index]
    sample_index = st.slider('Move along the recorded journey',0,max(1,len(row['trajectory'])-1),0,key='audit_sample.'+row['run_id'])
    sample_index = min(sample_index,len(row['trajectory'])-1)
    point = row['trajectory'][sample_index]
    from planning.core import distance_to_path
    error = distance_to_path((point['x'],point['y']),row['path']) if len(row.get('path',[]))>1 else None
    st.write(f"Checkpoint {sample_index}: simulation timestamp {point['t']:.1f} s. "
             +(f'Estimated path error {error:.2f} m.' if error is not None else 'No path error available.'))
    map_plot(st,row['map'],{'Planned':row.get('path',[]),'Executed':[(p['x'],p['y']) for p in row['trajectory']]},checkpoint=point)
    feature = st.radio('What is happening at your chosen checkpoint?',
        ['Straight segment','Turn','Detour','Tracking deviation','Stopped or failed approach'],horizontal=True,key='audit_feature')
    if st.button('Retain this checkpoint for my analysis'):
        audit = dict(run_id=row['run_id'],map=row['map'],planner=row['planner'],sample=sample_index,
                     point=point,tracking_error_m=error,feature=feature)
        st.session_state['settings']['navigation_inspection'] = audit
        atomic_json(submission_root()/'mission_2/route_inspection.json',audit)
        st.success('Checkpoint saved. Refer to this location in your first answer.')
    audit = st.session_state['settings'].get('navigation_inspection',{})
    return audit.get('run_id') in {r['run_id'] for r in rows}


def mission2(st):
    st.header('Mission 2: Execute navigation on two maps')
    st.write('A planned route is not a completed journey. Compare your four grid searches, supplied RRT and PRM, and Nav2 Smac 2D '
             'cost-aware A* with built-in smoothing. Every route uses the same Regulated Pure Pursuit FollowPath controller. Run all seven methods on both open and constrained '
             'maps, giving 14 experimental cells. Repeat if time permits. One trial does not establish a reliable success rate.')
    with st.expander('Where planning ends and path control begins'):
        from lab.planning_playground import architecture
        architecture(st)
        st.write('You supply or request a global route. The provided controller uses the current pose to issue motion commands '
                 'while checking nearby obstacles. These fixed-path trials compare execution, not a new global-replanning policy.')
    st.subheader('1. Understand the experiment and predict a result')
    st.write('If you completed the Environment check, setup is already done. No additional build or manual launch is needed here. '
             'The runner creates Gazebo walls and occupancy maps from the same '
             'geometry as Mission 1. Every attempt restarts the world, robot, AMCL and Nav2. Start and goal stay fixed. '
             'Do not launch mapping, teleop or another navigation process alongside the batch.')
    st.write('Imagine choosing a delivery route through a building. A global planner chooses where to go, while a controller '
             'continuously turns that route into forward and turning commands using the estimated robot position. '
             'Our supplied Regulated Pure Pursuit controller aims at a point ahead on the path and slows for turns and nearby obstacles. '
             'It does not replace your search code. Keeping this controller fixed helps isolate differences between routes. '
             'The destination test uses the same 0.25 m position tolerance for every planner. No final parking direction is required.')
    st.table(pd.DataFrame([
        ['BFS','Explores outward by move count with a queue, shortest on unit-cost grids'],
        ['DFS','Follows a branch with a stack, valid routes can be long'],
        ['IDDFS','Repeats bounded DFS, can spend much work revisiting cells'],
        ['A*','Prioritizes cost so far plus a lower-bound distance estimate'],
        ['RRT','Grows a tree toward randomly sampled free positions'],
        ['PRM','Connects sampled free positions into a roadmap and searches it'],
        ['Nav2 Smac 2D','Cost-aware A* with smoothing, a supplied system baseline']
    ],columns=['Planner','How it chooses a route']))
    st.write('Matched trials mean the map, start, goal, speed limit and controller stay the same while the planner changes. '
             'The open map permits more direct routes. The constrained map forces passages and turns. '
             'BFS and your A* should have equal shortest route lengths because both solve the same unit-cost graph. '
             'They can still expand different numbers of cells, choose different equally short routes, and execute differently.')
    a,b = st.columns(2)
    with a:
        map_plot(st,'open')
    with b:
        map_plot(st,'constrained')
    response(st,'mission_2.prediction','Before running: choose two planners. Which do you predict will finish sooner on the constrained map, '
             'and why? Use their Mission 1 results or the descriptions above. Your prediction does not have to be correct.')
    st.subheader('2. Run matched trials')
    st.write('In the ROS desktop terminal, inspect one trial first. Gazebo opens automatically. The tool waits for live data, plans, '
             'executes and stops. Each attempt gets its own directory and logs. Ctrl+C stops the batch.')
    st.code('cd /workspace/week09_planning_navigation\nbash scripts/run_trials.sh --mission 2 --planners nav2 --maps open --gui',language='bash')
    st.write('Then run the remaining comparison below. --skip-existing reuses matching recorded attempts, including your first Nav2 run. '
             'The terminal prints the current trial, remaining count, startup status and execution progress. '
             'All planners share a 0.30 m/s maximum speed and each robot trial has a 180 second simulated-time limit. '
             'Long or failed routes can still take time. Add --repeats 3 '
             'for three repeats. RRT and PRM use repeat indices as random seeds. Localization and simulation can still vary between '
             'resets. Keep your planner code fixed during the comparison. To retry one cell, add --planners bfs --maps constrained.')
    st.code('bash scripts/run_trials.sh --mission 2 --skip-existing',language='bash')
    st.write('A search that exhausts resources produces a planning outcome without moving the robot. environment_error means startup '
             'or live-data checks failed. Read launch.log and probe.log, fix the setup and rerun. Missing ROS actions are not planner failures.')
    st.subheader('3. Compare measurements')
    st.write('planning_s is computation time. Offline methods use a wall-clock timer. Nav2 reports its internal planning duration, '
             'with communication round-trip time stored separately in the raw result. elapsed_s is simulated execution time. distance_m is AMCL map-frame travel '
             'distance. planned_length_m is requested route length. goal_error_m is final estimated distance from the goal. '
             'mean_tracking_error_m is average distance to the nearest path segment. minimum_static_clearance_m estimates body clearance '
             'from mapped walls. minimum_lidar_range_m is a proximity proxy. '
             'A range below 0.10 m triggers a stop. This is not physical contact detection.')
    st.button('Refresh navigation trials')
    rows = trial_table(st,2)
    st.write('For each planner and map, divide succeeded outcomes by all valid attempts to estimate success rate. Compare time and '
             'distance for successful trials separately from failures. Also compare planning time and tracking error. '
             'The constrained map tests turns and passages absent from the open map. The same speed limit does not mean identical actual speeds.')
    st.subheader('4. Investigate one result')
    st.write('Choose your predicted pair in Inspect an attempt above. Compare their planned and executed lines. '
             'Look for an extra detour, tight turn, tracking deviation, or an early stop. Use the per-map bars to decide '
             'whether the larger difference is on the open or constrained map. Record what you observed below. '
             'If you want to investigate further, rerun only that planner/map pair, not the whole batch.')
    inspected = inspect_navigation(st,rows)
    a = response(st,'mission_2.performance','For your predicted pair on the constrained map, report each status, elapsed_s and distance_m. '
                 'Did the result support your prediction? Point to one turn, detour, tracking difference or stop in the attempt plots that helps explain it.')
    b = response(st,'mission_2.choice','Use the two map charts to choose a delivery planner. Report its status and execution time on each map. '
                 'Compare it with one alternative using distance or tracking error. What advantage matters most for your choice?')
    source = submission_root()/'mission_1/planners.py'
    checks = navigation_checks(rows,sha(source) if source.exists() else '')
    checks.append(('A trajectory checkpoint was inspected and retained',inspected))
    if rows and all(ok for _,ok in checks) and a and b:
        copy_trials(rows,'mission_2')
    finish(st,'mission_2',{'schema':2,'rows':[{k:v for k,v in r.items() if k!='_file'} for r in rows]},checks,a and b and bool(st.session_state['responses'].get('mission_2.prediction','').strip()))


def mission3(st):
    st.header('Mission 3: Human-aware potential fields')
    st.write('Imagine a delivery robot carrying supplies through a shared area. Its shortest route may squeeze past someone '
             'even though a wider detour is available. In this mission you will add a preference for personal space to existing routes, '
             'inspect how the routes change, then test whether those changes improve the robot journey. '
             'Choose at least two planners and compare each original route with two settings of a human-aware potential field.')
    from lab.planning_playground import navigation_responses
    navigation_responses(st)
    st.subheader('1. Inspect and configure the field')
    st.write('A potential field is an artificial landscape of attraction and repulsion. It is a planning tool, not a physical force. '
             'Human-unaware planners see the physical person as an obstacle, but have no personal-space preference. The potential '
             'field adds repulsion around people and attraction toward successive points on the original path. Both refined and '
             'baseline routes use the same controller. Edges remain collision checked. Fields can stall or oscillate. Keep those failures.')
    st.write('The attraction points toward the next original route waypoint. Repulsion points away from each person. '
             'Its strength grows as body clearance d gets smaller and is zero beyond influence distance R. The next refinement '
             'step follows the direction of the summed forces. Attraction and repulsion can cancel, which explains local minima.')
    st.latex(r'F_{\mathrm{repel}}=k\left(\frac{1}{d}-\frac{1}{R}\right)\frac{1}{d^2}\hat{u}_{\mathrm{away}},\quad 0<d<R')
    st.table(pd.DataFrame([
        ['k / human_gain','Repulsion strength. Larger values push the computed path away more strongly'],
        ['d','Body-to-body gap from this candidate robot position to the person, in metres'],
        ['R / influence_m','Gap at which repulsion begins. Outside this distance repulsion is zero'],
        ['unit vector away','Direction from the person toward the candidate robot position'],
        ['step_m','Distance advanced at each refinement iteration, not robot driving speed']
    ],columns=['Symbol or setting','Plain-language meaning']))
    st.write('You do not need to calculate the equation by hand. First change only repulsion strength and compare the map overlays. '
             'Then change influence distance. Look for a wider detour, an unchanged path, or a failed refinement where wall avoidance '
             'and human repulsion leave no useful direction. The start and goal remain fixed.')
    st.caption('The implementation bounds very small distances and caps repulsion to avoid numerical blow-up. '
               'Reference implementation: ros2_ws/src/week09_nav_tools/planning/social.py, refine().')
    saved_fields = st.session_state['settings'].get('fields',CONFIGS)
    fields = {'baseline':dict(CONFIGS['baseline'])}
    for column,label in zip(st.columns(2),('social_1','social_2')):
        with column:
            st.write('**'+label+'**')
            fields[label] = {
                'human_gain':st.slider('Repulsion strength',0.0,5.0,float(saved_fields[label]['human_gain']),.05,key=label+'.gain'),
                'influence_m':st.slider('Influence distance (m)',.1,3.0,float(saved_fields[label]['influence_m']),.1,key=label+'.influence'),
                'step_m':st.slider('Refinement step (m)',.01,.15,float(saved_fields[label]['step_m']),.01,key=label+'.step')}
    st.markdown('#### See how the artificial forces combine')
    from lab.planning_visuals import force_figure,show_figure
    show_figure(st,force_figure(fields))
    st.write('Both panels use the same example robot position and next original waypoint. The blue arrow attracts the candidate '
             'toward that waypoint. The orange arrow repels it away from the person. The green arrow is their vector sum. '
             'The dashed orange copy starts at the blue tip to show tip-to-tail addition. Change the sliders and compare '
             'the green direction in social_1 and social_2. The dotted circle marks where repulsion begins for the robot centre.')
    st.caption('Arrow lengths show relative artificial force strength, with a shared drawing scale. They are not metres or newtons. '
               'The black cross is the next proposed point, one step_m along the green direction. step_m changes that step, '
               'not force strength or robot speed. A proposed step still needs the collision check. This is one local example, not the whole route.')
    st.caption('Slider changes update both previews immediately. Save settings only when you have chosen the two configurations for robot trials.')
    for column,name in zip(st.columns(2),('open','constrained')):
        with column:
            grid = inflate(make_map(name,PEOPLE))
            base = [cell_to_world(p) for p in reference_path(grid)]
            paths = {'Baseline':base}
            for label in ('social_1','social_2'):
                diagnostic = {}
                points,status = refine(base,grid,PEOPLE,fields[label],diagnostic)
                paths[label if points else label+' (partial)'] = points or diagnostic.get('path',[])
                if points:
                    st.caption(f'{label}: {status}, complete preview path.')
                else:
                    st.warning(f'{label}: {status}. Dashed line shows where refinement got stuck, not a complete route. '
                               'Try less repulsion or a smaller influence distance. Failed refinements remain valid evidence.')
            map_plot(st,name,paths,PEOPLE)
    if st.button('Save field settings for robot trials'):
        if fields['social_1']==fields['social_2'] or any(fields[label]==fields['baseline'] for label in ('social_1','social_2')):
            st.error('Choose two distinct social configurations, both different from baseline.')
        else:
            atomic_json(submission_root()/'mission_3/potential_fields.json',fields)
            st.session_state['settings']['fields'] = fields
            st.success('Settings saved. The terminal runner reads this JSON automatically.')
    st.write('Orange circles show bodies. Dotted circles mark 0.75 m body-to-body personal space, including robot radius. '
             'This threshold is an experimental choice, not a universal comfort rule.')
    prediction = response(st,'mission_3.prediction','Change one slider at a time. Report the setting before and after, the map you inspected, '
                          'and what changed in the path. Did it move farther from the person, stay the same, or get stuck? Use the map and status shown above.')
    st.subheader('2. Run paired trials')
    if not (submission_root()/'mission_3/potential_fields.json').exists():
        st.info('Select Save field settings for robot trials above. This creates the JSON read by the terminal runner.')
    st.write('Select at least two planners, for example A* and RRT, on one or both maps. The command runs baseline, social_1 and '
             'social_2 with matching planner, seed, map, start and goal, resetting before each. Keep configurations fixed across planners. '
             'Gazebo and progress messages are enabled by default. The same 0.30 m/s limit applies to every condition. '
             '--skip-existing skips only attempts that already match your saved settings and current code. Changing a field '
             'reruns that condition without repeating unchanged cells. The example requires six trials, not all seven planners on both maps.')
    st.code('bash scripts/run_trials.sh --mission 3 --planners astar rrt --maps open --skip-existing --fields student_submission/mission_3/potential_fields.json',language='bash')
    st.subheader('3. Compare social and navigation outcomes')
    st.write('minimum_person_clearance_m subtracts both body radii from centre distance. Negative means estimated overlap. '
             'personal_space_s counts simulated seconds below the 0.75 m clearance threshold. max_speed_near_people_mps is the '
             'highest odometry speed inside that threshold. Read these alongside success, time, distance and field failure status. '
             'A failed trial with no motion is not socially superior simply because exposure is zero.')
    st.button('Refresh social trials')
    rows = trial_table(st,3)
    st.write('For each planner, read the baseline, social_1 and social_2 rows together. Higher minimum_person_clearance_m means '
             'more space at the closest pass. Lower personal_space_s means less time inside the chosen threshold. '
             'Use elapsed_s or distance_m to see what that spacing cost. Start with status so a stationary failure is not mistaken for an improvement.')
    a = response(st,'mission_3.comparison','For each of your two planners, name the completed condition with the largest minimum_person_clearance_m. '
                 'Compare that value and personal_space_s with its baseline row. Did the wider spacing cost more time or distance? '
                 'If a condition failed, report its status instead of ranking it as an improvement.')
    b = response(st,'mission_3.recommendation','Which condition would you keep for this scenario? Give its planner, status, minimum clearance '
                 'and time or distance from the table. Compare it with one alternative. What can these static-person trials not tell you about moving people?')
    checks = social_checks(rows)
    source = submission_root()/'mission_1/planners.py'
    checks.append(('Student source is current',all(r.get('planner') not in ('bfs','dfs','iddfs','astar') or
        source.exists() and r.get('source_sha256')==sha(source) for r in rows)))
    checks.append(('Saved field settings match selected trials',(submission_root()/'mission_3/potential_fields.json').exists() and
        all(r.get('condition') in fields and r.get('field_hash')==fingerprint(fields[r['condition']]) for r in rows)))
    if rows and all(ok for _,ok in checks) and a and b:
        copy_trials(rows,'mission_3')
    finish(st,'mission_3',{'schema':2,'rows':[{k:v for k,v in r.items() if k!='_file'} for r in rows]},checks,prediction and a and b)


def final(st):
    from lab.final_reflection import render_final_reflection, write_final_reflection
    st.header('Synthesis and submission')
    response(st,'final.synthesis','Across all three missions, what makes a route suitable for a robot sharing space with people? Connect search efficiency and route quality, navigation on both maps and social field trade-offs. Use specific results and distinguish estimates from ground truth.')
    reflection_ready = render_final_reflection(st)
    for key,label in [('name','Your name'),('email','Student ID or email')]:
        widget = 'identity.'+key
        if widget not in st.session_state:
            st.session_state[widget] = st.session_state['student'].get(key,'')
        st.session_state['student'][key] = st.text_input(label,key=widget)
    evidence = st.session_state['evidence']
    source = submission_root()/'mission_1/planners.py'
    m1 = evidence.get('mission_1',{})
    m2 = evidence.get('mission_2',{}).get('rows',[])
    m3 = evidence.get('mission_3',{}).get('rows',[])
    current_hash = sha(source) if source.exists() else ''
    fields = st.session_state['settings'].get('fields',{})
    checks = [('Mission 1 results match source',all(v for _,v in offline_checks(m1)) and bool(current_hash) and m1.get('source_sha256')==current_hash),
              ('Mission 2 matched trials',all(v for _,v in navigation_checks(m2,current_hash))),
              ('Mission 3 matched trials',all(v for _,v in social_checks(m3))),
              ('Mission 3 student source is current',all(r.get('planner') not in ('bfs','dfs','iddfs','astar') or r.get('source_sha256')==current_hash for r in m3)),
              ('Mission 3 field settings are current',bool(fields) and all(r.get('condition') in fields and
                   r.get('field_hash')==fingerprint(fields[r['condition']]) for r in m3)),
              ('Selected raw trial files are saved',trial_files_ready('mission_2',m2) and trial_files_ready('mission_3',m3)),
              ('Navigation checkpoint retained',st.session_state['settings'].get('navigation_inspection',{}).get('run_id') in {r['run_id'] for r in m2}),
              ('Technical synthesis',bool(st.session_state['responses'].get('final.synthesis','').strip())),
              ('Individual reflection: 1 to 300 words',reflection_ready),
              ('Mission explanations remain complete',all(str(st.session_state['responses'].get(key,'')).strip() for key in
                  ['mission_1.search','mission_1.failure','mission_2.prediction','mission_2.performance','mission_2.choice','mission_3.prediction','mission_3.comparison','mission_3.recommendation'])),
              ('Name and student ID or email',all(v.strip() for v in st.session_state['student'].values()))]
    ready = checks_table(st,checks)
    st.write('There is one ZIP download. It contains your current saved files. If all checks pass it is marked complete. '
             'Otherwise it is marked incomplete and is a backup, not a finished submission. Prepare it again after making changes.')
    if st.button('Save and prepare ZIP',type='primary'):
        for mission in ('mission_1','mission_2','mission_3'):
            if mission in evidence:
                save_evidence(mission,evidence[mission],st.session_state['responses'])
                write_reports(mission,evidence[mission])
        (submission_root()/'technical_synthesis.md').write_text(st.session_state['responses'].get('final.synthesis',''),encoding='utf-8')
        if reflection_ready:
            write_final_reflection(st)
        else:
            (submission_root()/'final_reflection.md').write_text(st.session_state['responses'].get('final.course_reflection',''),encoding='utf-8')
        st.session_state['submission_zip'] = export(st.session_state,ready)
        st.session_state['zip_ready'] = ready
    if st.session_state.get('submission_zip'):
        st.caption('Prepared archive status: '+('complete' if st.session_state.get('zip_ready') else 'incomplete backup'))
        st.download_button('Download submission ZIP',st.session_state['submission_zip'],'lab8_submission.zip','application/zip')
    st.write('Your submission includes planner source, search results, robot trial evidence, field configurations, answers and reflection. '
             'Do not commit ROS build or runtime files. student_submission is not ignored by Git.')
    st.code('git add week09_planning_navigation/student_submission\ngit commit -m "Submit Lab 8"\ngit push',language='bash')
    st.write('Run Git commands from the repository root on your host. Submit the required commit link.')


PAGES = [intro,concepts,preflight,mission1,mission2,mission3,final]


def main():
    import streamlit as st
    st.set_page_config(page_title='Lab 8: Planning and Human-Aware Navigation',page_icon='🧭',layout='wide')
    ensure_planner_source()
    if not st.session_state.get('initialized_v2'):
        try:
            saved = load()
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        for key,default in [('stage','intro'),('student',{'name':'','email':''}),('responses',{}),('evidence',{}),('completed_missions',[]),('settings',{})]:
            st.session_state[key] = saved.get(key,default)
        if st.session_state['stage'] not in STAGES:
            st.session_state['stage'] = 'intro'
        st.session_state['notice'] = saved.get('migration_notice','')
        st.session_state['initialized_v2'] = True
    stage = st.session_state['stage']
    if stage!='concepts':
        st.session_state['demo_playing'] = False
    index = STAGES.index(stage)
    st.progress((index+1)/len(STAGES),text=f'{index+1}/{len(STAGES)}: {LABELS[index]}')
    if st.session_state['notice']:
        st.info(st.session_state['notice'])
    for i,label in enumerate(LABELS):
        if st.sidebar.button(label,key=f'navigation{i}',disabled=i==index):
            st.session_state['stage'] = STAGES[i]
            save(st.session_state)
            st.rerun()
    PAGES[index](st)
    page_location = (stage,st.session_state['settings'].get('planning_activity',0) if stage=='concepts' else None)
    if st.session_state.get('previous_stage') != page_location:
        import uuid
        st.html('<script>(()=>{// '+uuid.uuid4().hex+'\n'
                'const reset=()=>{window.scrollTo(0,0); document.querySelectorAll(\'[data-testid="stMain"], '
                '[data-testid="stAppViewContainer"], section.main\').forEach(el=>el.scrollTo({top:0,behavior:"instant"}));}; '
                'requestAnimationFrame(reset); setTimeout(reset,100); setTimeout(reset,300); setTimeout(reset,700);})();</script>',unsafe_allow_javascript=True)
        st.session_state['previous_stage'] = page_location
    st.divider()
    left,right = st.columns(2)
    with left:
        if index and st.button('Back to '+LABELS[index-1],width='stretch'):
            st.session_state['stage'] = STAGES[index-1]
            save(st.session_state)
            st.rerun()
    with right:
        blocked = stage.startswith('mission_') and stage not in st.session_state['completed_missions']
        if index<len(STAGES)-1 and st.button('Next: '+LABELS[index+1],disabled=blocked,width='stretch'):
            st.session_state['stage'] = STAGES[index+1]
            save(st.session_state)
            st.rerun()
    try:
        save(st.session_state)
        st.sidebar.caption('Progress saved locally')
    except OSError as exc:
        st.error(f'Progress could not be saved: {exc}. Keep this page open and make a backup.')
