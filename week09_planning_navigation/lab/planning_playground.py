"""Five guided, ungraded activities and a reusable navigation-system diagram."""
import matplotlib.pyplot as plt
import math
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle, FancyBboxPatch
import pandas as pd
from planning.core import neighbours, free, inflate, reference_path, RESOLUTION, fingerprint
from planning.teaching import teaching_map, search_trace, weighted_case, footprint_case


def grid_figure(grid,start,goal,title='',frame=None,costs=None,selected=None,compact=False):
    fig,ax = plt.subplots(figsize=(4,3) if compact else (6,3.5))
    rows,cols = len(grid),len(grid[0])
    ax.imshow(grid,origin='lower',cmap=ListedColormap(['#fafafa','#343a40']),vmin=0,vmax=1)
    if costs:
        for r in range(rows):
            for c in range(cols):
                if not grid[r][c] and costs[r][c]>1:
                    ax.add_patch(Rectangle((c-.5,r-.5),1,1,color='#f6db92'))
                if not grid[r][c]:
                    ax.text(c,r,str(costs[r][c]),ha='center',va='center',fontsize=8)
    if frame:
        for key,color in [('explored','#a8d7f0'),('frontier','#ffd27f')]:
            for r,c in frame.get(key,[]):
                ax.add_patch(Rectangle((c-.46,r-.46),.92,.92,color=color,alpha=.8))
        path = frame.get('path',[])
        if path:
            ax.plot([p[1] for p in path],[p[0] for p in path],color='#139753',linewidth=2)
        if frame.get('current') is not None:
            r,c = frame['current']
            ax.add_patch(Rectangle((c-.47,r-.47),.94,.94,fill=False,edgecolor='#d22f45',linewidth=2))
    if selected is not None:
        r,c = selected
        ax.add_patch(Rectangle((c-.45,r-.45),.9,.9,fill=False,edgecolor='#d22f45',linewidth=2))
        for rr,cc in neighbours(grid,selected):
            ax.add_patch(Rectangle((cc-.43,rr-.43),.86,.86,fill=False,edgecolor='#eea600',linewidth=2))
    for point,label,color in [(start,'S','#006735'),(goal,'G','#9e1338')]:
        r,c = point
        if start==goal:
            label = 'S=G'
        ax.text(c,r,label,ha='center',va='center',fontsize=9,fontweight='bold',color=color,
                bbox=dict(facecolor='white',alpha=.8,edgecolor='none',pad=.2))
    ax.set_xticks(range(cols))
    ax.set_yticks(range(rows))
    ax.set_xticks([v-.5 for v in range(cols+1)],minor=True)
    ax.set_yticks([v-.5 for v in range(rows+1)],minor=True)
    ax.grid(which='minor',color='#b8bec5',linewidth=.4)
    ax.tick_params(which='minor',length=0)
    ax.set(xlabel='column',ylabel='row',title=title,xlim=(-.5,cols-.5),ylim=(-.5,rows-.5))
    fig.tight_layout()
    return fig


def show_grid(st,*args,**kwargs):
    fig = grid_figure(*args,**kwargs)
    st.pyplot(fig,width=620)
    plt.close(fig)


def architecture(st):
    fig,ax = plt.subplots(figsize=(10,3.2))
    ax.set(xlim=(0,1),ylim=(-.1,1))
    ax.axis('off')
    nodes = [( .1,.68,'Sensor observations\nSupplied','#dbeafa'),(.3,.68,'Map / costmap\nSupplied','#dbeafa'),
             (.5,.68,'Global planner\nM1: your searches','#dbefde'),(.7,.68,'Path controller\nM2: supplied','#fbe9c8'),
             (.9,.68,'Robot motion\nSimulation','#e7e3f7'),(.3,.25,'Pose estimate\nLocalization supplied','#dbeafa')]
    for x,y,label,color in nodes:
        ax.add_patch(FancyBboxPatch((x-.085,y-.11),.17,.22,boxstyle='round,pad=.008',facecolor=color,edgecolor='#667085'))
        ax.text(x,y,label,ha='center',va='center',fontsize=8)
    arrow = dict(arrowstyle='->',color='#505969',lw=1.3)
    for x in (.1,.3,.5,.7):
        ax.annotate('',xy=(x+.108,.68),xytext=(x+.09,.68),arrowprops=arrow)
    ax.annotate('',xy=(.25,.36),xytext=(.1,.56),arrowprops=arrow)
    ax.annotate('',xy=(.5,.56),xytext=(.35,.36),arrowprops=arrow)
    ax.annotate('',xy=(.64,.56),xytext=(.36,.56),arrowprops=dict(arrowstyle='->',color='#667085',lw=1,
                 linestyle='--',connectionstyle='arc3,rad=.25'))
    ax.text(.50,.44,'local obstacle costs',ha='center',fontsize=7,color='#505969',
            bbox=dict(facecolor='white',edgecolor='none',pad=.2))
    ax.annotate('',xy=(.7,.56),xytext=(.38,.25),arrowprops=arrow)
    ax.text(.58,.20,'estimated pose',fontsize=8,color='#505969')
    ax.text(.60,.94,'M3: human-aware path refinement\nusing known person locations',ha='center',fontsize=8)
    ax.annotate('',xy=(.6,.72),xytext=(.6,.85),arrowprops=arrow)
    ax.plot([.9,.9,.1,.1],[.56,.02,.02,.56],color='#505969',lw=1)
    ax.annotate('',xy=(.1,.56),xytext=(.1,.45),arrowprops=arrow)
    ax.text(.5,-.035,'Motion changes observations, which update the map and pose estimate',ha='center',fontsize=8)
    fig.tight_layout()
    st.pyplot(fig,width=1000)
    plt.close(fig)
    st.caption('Your search code chooses a route, not motor commands. Mission 2 supplies localization, sensing and path control. '
               'The controller uses the pose estimate and local obstacle costs. Mission 3 adds a human-aware path refinement '
               'before that same controller.')


def navigation_responses(st):
    st.subheader('Different obstacles can call for different responses')
    fig,axes = plt.subplots(1,3,figsize=(10,2.7))
    from matplotlib.patches import Circle
    for ax,title in zip(axes,['Permanent obstruction','Person temporarily crossing','Person occupying shared space']):
        ax.set(xlim=(0,10),ylim=(-2,2.3),title=title,aspect='equal')
        ax.axhline(0,color='#7b8794',linestyle=':',linewidth=1)
        ax.add_patch(Circle((1,0),.25,color='#326cc0'))
        ax.text(1,-.55,'Robot',ha='center',fontsize=8)
        ax.scatter([9],[0],marker='*',c='green')
        ax.text(9,-.55,'Goal',ha='center',fontsize=8)
        ax.set_xticks([])
        ax.set_yticks([])
    axes[0].add_patch(Rectangle((4.7,-1.8),.6,3.6,color='#59636f'))
    axes[1].add_patch(Circle((5,0),.25,color='#eb9d37'))
    axes[1].annotate('',xy=(5,1.5),xytext=(5,-1.5),arrowprops=dict(arrowstyle='->',color='#eb9d37',lw=2))
    axes[2].add_patch(Circle((5,.9),.25,color='#eb9d37'))
    axes[2].add_patch(Circle((5,.9),1.18,fill=False,linestyle=':',color='#eb9d37'))
    axes[2].plot([1,3,5,7,9],[0,-.3,-.5,-.3,0],color='#139753')
    fig.tight_layout()
    st.pyplot(fig,width=1000)
    plt.close(fig)
    first,second,third = st.columns(3)
    first.write('**Permanent obstruction:** stop if the route is blocked. Updated map evidence may justify a new global route '
                'from the current pose. If no route exists, report failure rather than keep moving.')
    second.write('**Temporary crossing:** slowing or stopping and waiting can be preferable to a large detour. '
                 'Local avoidance needs sufficient fresh evidence and room. Never assume a person will move away.')
    third.write('**Person occupying an area:** a collision-free route may still pass too close. A human-aware route can '
                'leave more space, at the cost of distance or time. Appropriate spacing depends on context.')


def editor(st):
    st.subheader('1. Turn an environment into a planning problem')
    st.write('A grid stores one value for each cell. Here 0 means free and 1 means occupied. A position is (row, column), '
             'with row 0 at the bottom of the picture. Four-connected movement means up, down, left or right. '
             'A legal neighbor must stay inside the grid and cannot be occupied.')
    settings = st.session_state['settings']
    if st.button('Reset teaching map'):
        settings['teaching_grid'] = teaching_map()
        settings['teaching_start'],settings['teaching_goal'] = [2,1],[2,9]
        settings['editor_revision'] = settings.get('editor_revision',0)+1
        for key in ('toy_sr','toy_sc','toy_gr','toy_gc'):
            st.session_state.pop(key,None)
    grid = settings.get('teaching_grid',teaching_map())
    st.write('Your goal is to discover what makes a route possible. Draw a wall that forces a detour, then close the last opening. '
             'Predict whether the robot can still reach G from S and press Show plan to check. Reopen a gap and try again. '
             'This is a supplied planner so you can explore the problem before implementing a search yourself.')
    start,goal = settings.get('teaching_start',[2,1]),settings.get('teaching_goal',[2,9])
    from pathlib import Path
    component = st.components.v2.component('lab8_grid_editor',
        html='<label>Drawing tool <select><option value="wall">Add walls</option><option value="erase">Remove walls</option><option value="start">Place start</option><option value="goal">Place goal</option></select></label><br><canvas aria-label="Editable planning grid"></canvas>',
        css='select {margin:8px;padding:6px} canvas {cursor:crosshair;border:1px solid #667085}',
        js=(Path(__file__).with_name('grid_editor.js')).read_text())
    key = 'draw_grid_'+str(settings.get('editor_revision',0))
    initial = dict(grid=grid,start=list(start),goal=list(goal))
    widget = st.session_state.get(key,{})
    incoming = widget.get('state',initial) if isinstance(widget,dict) else initial
    result = component(key=key,data={'state':incoming},default={'state':initial},on_state_change=lambda:None,height='content')
    state = result.get('state',initial)
    grid,start,goal = state['grid'],tuple(state['start']),tuple(state['goal'])
    settings.update(teaching_grid=grid,teaching_start=start,teaching_goal=goal)
    st.caption('Choose a drawing tool. Click or drag to paint cells. Start and goal tools place one endpoint with a click. Changes are saved when you release the pointer.')
    show = st.button('Show plan',key='toy_show_plan')
    path = reference_path(grid,start,goal)
    if show:
        show_grid(st,grid,start,goal,'Supplied BFS plan',frame={'path':path})
    if not free(grid,start) or not free(grid,goal):
        st.warning('Start or goal is occupied. Change its coordinates or clear that cell.')
    elif show:
        st.caption(f'A route exists with {len(path)-1} moves.' if path else 'Both endpoints are free, but no route connects them.')


def neighbor_activity(st):
    st.subheader('2. How does one cell connect to the next?')
    st.write('A search does not see a route all at once. At each cell it asks which single moves are legal. '
             'Those neighboring cells form the graph edges that every search will use. Inspect a cell beside a wall and then one '
             'at an edge. Notice which of the four possible moves is removed. Diagonal moves are not allowed.')
    settings = st.session_state['settings']
    grid = settings.get('teaching_grid',teaching_map())
    row = st.slider('Cell row',0,len(grid)-1,2,key='toy_neighbor_row')
    col = st.slider('Cell column',0,len(grid[0])-1,1,key='toy_neighbor_col')
    legal = neighbours(grid,(row,col)) if free(grid,(row,col)) else []
    st.write(f'Cell ({row}, {col}) has legal moves to {legal}.')
    if not free(grid,(row,col)):
        st.info('This is a wall, not a place the robot can occupy.')
    show_grid(st,grid,settings.get('teaching_start',[2,1]),settings.get('teaching_goal',[2,9]),
              'Red: selected cell. Gold: legal next cells',selected=(row,col) if free(grid,(row,col)) else None)
    st.write('In Mission 1, ctx.expand returns this list for your current cell. Your algorithm decides which candidate to examine next.')


def playback(st,grid,start,goal,method,costs=None):
    signature = fingerprint([grid,start,goal,method,costs])
    if st.session_state.get('demo_signature')!=signature:
        st.session_state['demo_trace'] = search_trace(grid,start,goal,method,costs)
        st.session_state['demo_signature'] = signature
        st.session_state['demo_frame'] = 0
        st.session_state['demo_playing'] = False
    trace = st.session_state['demo_trace']
    @st.fragment(run_every=.4 if st.session_state.get('demo_playing') else None)
    def player():
        last = len(trace['frames'])-1
        if st.session_state.get('demo_playing'):
            st.session_state['demo_frame'] = min(last,st.session_state['demo_frame']+1)
            if st.session_state['demo_frame']==last:
                st.session_state['demo_playing'] = False
                st.rerun()
        buttons = st.columns(4)
        if buttons[0].button('Reset search',key='demo_reset'):
            st.session_state['demo_frame'],st.session_state['demo_playing'] = 0,False
            st.rerun()
        if buttons[1].button('Step',key='demo_step',disabled=st.session_state['demo_frame']>=last):
            st.session_state['demo_frame'] += 1
        if buttons[2].button('Pause' if st.session_state.get('demo_playing') else 'Play',key='demo_play'):
            st.session_state['demo_playing'] = not st.session_state.get('demo_playing',False)
            if st.session_state['demo_frame']==last:
                st.session_state['demo_frame'] = 0
            st.rerun()
        if buttons[3].button('Show final result',key='demo_end'):
            st.session_state['demo_frame'],st.session_state['demo_playing'] = last,False
            st.rerun()
        frame = trace['frames'][st.session_state['demo_frame']]
        show_grid(st,grid,start,goal,method.upper()+' search',frame=frame,costs=costs)
        st.caption('Light blue: expanded cells. Orange: frontier. Red outline: current cell. Green line: current parent chain, '
                   'which becomes the returned path only when the goal is reached. S: start. G: goal.')
        st.write(f"Frame {st.session_state['demo_frame']+1}/{last+1}. Expanded nodes: {frame['expanded']}. "
                 f"Current cell: {frame['current']}. Pending frontier cells shown: {len(frame['frontier'])}. Status: {frame['status']}.")
        if frame['depth_limit'] is not None:
            st.caption(f"IDDFS depth limit: {frame['depth_limit']}. Shading resets at each depth bound. The expansion count includes repeated work.")
    player()
    return trace


def searches(st):
    st.subheader('3. Watch the frontier and exploration order')
    st.write('The frontier stores candidates waiting to be examined. Expanded cells have had their successors considered. '
             'Parent links record how a candidate was reached. The green chain is not necessarily the final route until the goal is selected.')
    st.write('BFS removes the oldest candidate from a queue. DFS removes the newest candidate from a stack. IDDFS repeats '
             'depth-limited DFS with increasing bounds. A* removes the candidate with lowest g + h from a priority queue. '
             'Here g counts moves so far and h is Manhattan distance to the goal.')
    method = st.selectbox('Supplied reference method',['bfs','dfs','iddfs','astar'],format_func=str.upper,key='demo_method')
    settings = st.session_state['settings']
    grid = settings.get('teaching_grid',teaching_map())
    start,goal = settings.get('teaching_start',[2,1]),settings.get('teaching_goal',[2,9])
    st.write('Predict which direction this method will explore first. Step through its operations or press Play. '
             'Switch methods to compare the same grid. Return to Activity 1 to change the planning problem.')
    playback(st,grid,start,goal,method)
    results = [search_trace(grid,start,goal,m) for m in ('bfs','dfs','iddfs','astar')]
    st.dataframe(pd.DataFrame([{k:result[k] for k in ('method','status','steps','expanded','peak_frontier')} for result in results]),hide_index=True,width='stretch')
    st.caption('All demonstrations use the same neighbor order. DFS pushes neighbors in reverse so the first neighbor is visited first. '
               'Reference demos stop at 2,500 expansions. A resource limit is not proof that no path exists. Your own mission code runs separately.')


def weighted(st):
    st.subheader('4. Compare shortest distance with lowest cost')
    st.write('An occupied cell is forbidden. A costly cell is allowed, but undesirable. In this example the direct aisle has a higher '
             'entry cost than the surrounding floor. Costs might represent rough ground or a slow zone. They are not physical distances.')
    cost = st.select_slider('Entry cost in the highlighted aisle',options=[1.0,1.1,1.2,1.3,1.5,2.0],value=1.3,key='weighted_entry_cost')
    grid,costs,start,goal = weighted_case(cost)
    results = [search_trace(grid,start,goal,m,costs) for m in ('bfs','dijkstra','astar')]
    for column,result in zip(st.columns(3),results):
        with column:
            show_grid(st,grid,start,goal,result['method'].upper(),frame={'path':result['path']},costs=costs,compact=True)
    st.dataframe(pd.DataFrame([{k:r[k] for k in ('method','status','steps','total_cost','expanded')} for r in results]),hide_index=True,width='stretch')
    st.write('BFS minimizes the number of moves because its queue does not prioritize traversal cost. Dijkstra prioritizes g, '
             'the accumulated entry cost. A* prioritizes g + h. Here h is Manhattan distance multiplied by the smallest free-cell '
             'entry cost, so it does not overestimate the remaining cost. Dijkstra and A* should return the same minimum total cost, '
             'though ties can give different routes. A* does not always expand fewer nodes on every map.')
    st.write('At cost 1 the direct route costs 8. At 1.2 it costs 9.4 and is still cheaper than the 10-cost detour. '
             'At 1.3 it costs 10.1, so the minimum-cost methods switch to the detour. BFS keeps the eight-move route. '
             'The start cell has no entry charge. This supplied experiment is not an additional implementation task.')


def footprints(st):
    st.subheader('5. Give the robot a body')
    st.write('A point can pass through any connected chain of free cells. A physical robot needs room for its body. '
             'Obstacle inflation marks extra cells unavailable so a point representing the robot centre stays away from obstacles.')
    radius = st.radio('Conservative planning radius (m)',[0.0,.18,.30],index=1,horizontal=True,format_func=lambda v:f'{v:.2f} m',key='teaching_radius')
    raw,start,goal = footprint_case()
    enlarged = inflate(raw,radius)
    original_path,body_path = reference_path(raw,start,goal),reference_path(enlarged,start,goal)
    left,right = st.columns(2)
    with left:
        show_grid(st,raw,start,goal,'Original grid: point robot',frame={'path':original_path})
    with right:
        show_grid(st,enlarged,start,goal,f'Inflated grid: radius {radius:.2f} m',frame={'path':body_path})
    st.write(f'Each cell is {RESOLUTION:.2f} m wide. Square inflation adds {math.ceil(radius/RESOLUTION)} cell(s) in each direction. '
             'It is conservative for a circular robot, so the change occurs in discrete cell-sized jumps.')
    st.success('A route remains after inflation.') if body_path else st.warning('The passage is unavailable at this planning radius. The point-robot route is not a feasible body route.')
    st.write('Try radius 0, 0.18 and 0.30 m. Compare both images, not just route length. This teaching choice does not change '
             'the fixed 0.18 m planning radius used for graded search and robot trials.')


def render(st):
    st.header('Guided planning playground')
    st.write('Explore the representations and search operations before writing your own algorithms. Each activity explains a different '
             'part of planning. There are no written tutorial responses to submit.')
    settings = st.session_state['settings']
    part = min(4,max(0,int(settings.get('planning_activity',0))))
    st.caption(f'Activity {part+1} of 5')
    (editor,neighbor_activity,searches,weighted,footprints)[part](st)
    st.divider()
    left,right = st.columns(2)
    if part and left.button('Back to activity '+str(part),key='tutorial_back',width='stretch'):
        settings['planning_activity'] = part-1
        st.session_state['demo_playing'] = False
        st.session_state['previous_stage'] = None
        st.rerun()
    if part<4 and right.button('Continue to activity '+str(part+2),key='tutorial_next',width='stretch'):
        settings['planning_activity'] = part+1
        st.session_state['demo_playing'] = False
        st.session_state['previous_stage'] = None
        st.rerun()
    if part==4:
        st.info('You have reached the end of the playground. Continue to the environment check using the page button below.')
