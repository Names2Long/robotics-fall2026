"""Scientific teaching figures backed by the same context and field code as the lab."""
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
from planning.core import SearchContext, ROBOT_RADIUS
from planning.social import field_forces, PEOPLE


def context_handoff_figure():
    fig,ax = plt.subplots(figsize=(10,2.5))
    ax.set(xlim=(0,10),ylim=(0,2.5))
    ax.axis('off')
    boxes = [(.1,2.5,'Supplied test runner\nCreates a fresh problem'),
             (3.2,3.4,'ctx: your problem packet\nMap + start + goal\nLegal-move tool + distance estimate\nSearch-work counters'),
             (7.2,2.6,'Your bfs(ctx), dfs(ctx),\niddfs(ctx), or astar(ctx)\nChooses the search order')]
    for x,width,label in boxes:
        ax.add_patch(FancyBboxPatch((x,.65),width,1.45,boxstyle='round,pad=.04',facecolor='#eaf2fa',edgecolor='#52718f'))
        ax.text(x+width/2,1.38,label,ha='center',va='center',fontsize=10)
    for left,right,label in [(2.65,3.13,'passes'),(6.65,7.13,'uses')]:
        ax.annotate('',xy=(right,1.4),xytext=(left,1.4),arrowprops=dict(arrowstyle='->',lw=1.5))
        ax.text((left+right)/2,1.85,label,ha='center',fontsize=9)
    ax.text(5,.18,'Your frontier, visited cells, parents and g costs belong to your algorithm, not to ctx.',ha='center',fontsize=10)
    fig.tight_layout()
    return fig


def context_example():
    grid = [[int(r in (0,5) or c in (0,6) or (c==3 and r<4)) for c in range(7)] for r in range(6)]
    ctx = SearchContext(grid,start=(2,1),goal=(2,5))
    current = (2,2)
    adjacent = ctx.expand(current,5)
    return ctx,current,adjacent


def context_example_figure():
    from lab.planning_playground import grid_figure
    ctx,current,adjacent = context_example()
    fig = grid_figure(ctx.grid,ctx.start,ctx.goal,'One call to ctx.expand',selected=current,compact=True)
    fig.set_size_inches(5,3.6)
    ax = fig.axes[0]
    for nxt in adjacent:
        ax.annotate('',xy=(nxt[1],nxt[0]),xytext=(current[1],current[0]),
                    arrowprops=dict(arrowstyle='->',color='#936200',lw=1.7))
    fig.tight_layout()
    return fig


def force_figure(fields):
    """Compare the two live configurations at exactly the same example pose."""
    current,waypoint = (-.8,-1.05),(1.2,-1.05)
    person = PEOPLE[0]
    scale = .45
    fig,axes = plt.subplots(1,2,figsize=(10,4.6))
    reach = max(fields[label]['influence_m'] for label in ('social_1','social_2'))+person['radius']+ROBOT_RADIUS
    radius = max(2.3,reach+.35)
    colors = {'attraction':'#2369aa','repulsion':'#c06c10','resultant':'#178146'}
    for ax,label in zip(axes,('social_1','social_2')):
        config = fields[label]
        vectors = field_forces(current,waypoint,PEOPLE,config)
        influence = config['influence_m']+person['radius']+ROBOT_RADIUS
        ax.add_patch(Circle((person['x'],person['y']),influence,fill=False,ls=':',color='#c06c10',label='Influence boundary'))
        ax.add_patch(Circle((person['x'],person['y']),person['radius'],color='#edb76c'))
        ax.text(person['x'],person['y']-.45,'Person',ha='center',fontsize=9)
        ax.add_patch(Circle(current,ROBOT_RADIUS,color='#586779'))
        ax.text(current[0],current[1]-.38,'Candidate robot position',ha='center',fontsize=8)
        ax.scatter([waypoint[0]],[waypoint[1]],marker='*',s=100,color=colors['attraction'])
        ax.annotate('Next original waypoint',waypoint,xytext=(0,-24),ha='center',textcoords='offset points',fontsize=8)
        ax.plot([current[0],waypoint[0]],[current[1],waypoint[1]],ls='--',lw=.8,color='#9ba3ab')
        for key in ('attraction','repulsion','resultant'):
            vector = vectors[key]
            end = (current[0]+scale*vector[0],current[1]+scale*vector[1])
            ax.annotate('',xy=end,xytext=current,arrowprops=dict(arrowstyle='-|>',color=colors[key],lw=2.8 if key=='resultant' else 1.8))
            ax.plot([],[],color=colors[key],lw=2,label=key.capitalize())
        # Tip-to-tail copies make vector addition visible without changing magnitudes.
        a,r = vectors['attraction'],vectors['repulsion']
        ax.plot([current[0]+scale*a[0],current[0]+scale*(a[0]+r[0])],
                [current[1]+scale*a[1],current[1]+scale*(a[1]+r[1])],ls='--',lw=1,color=colors['repulsion'])
        length = math.hypot(*vectors['resultant'])
        if length>1e-6:
            step = tuple(current[i]+config['step_m']*vectors['resultant'][i]/length for i in (0,1))
            ax.plot([step[0]],[step[1]],marker='X',markersize=7,color='#161b22',
                    markeredgecolor='white',markeredgewidth=.8,linestyle='none',label='Next proposed point')
        ax.set(xlim=(-radius,radius),ylim=(person['y']-radius,person['y']+radius),aspect='equal',
               xlabel='x (m)',ylabel='y (m)',title=f"{label}: gain {config['human_gain']:.2f}, influence {config['influence_m']:.2f} m")
        ax.legend(fontsize=8,loc='lower right')
        ax.grid(alpha=.15)
    fig.tight_layout()
    return fig


def show_figure(st,figure,width=980):
    st.pyplot(figure,width=width)
    plt.close(figure)
