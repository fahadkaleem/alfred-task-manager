Directory structure:
└── pytransitions-transitions-gui/
    ├── README.md
    └── examples/
        ├── hsm.py
        ├── multiple.py
        ├── parallel.py
        ├── process.py
        ├── simple.py
        └── styling.py


Files Content:

================================================
FILE: README.md
================================================

# transitions-gui - A frontend for [transitions](https://github.com/pytransitions/transitions) state machines
[![Version](https://img.shields.io/badge/version-v0.9.0-orange.svg)](https://github.com/pytransitions/transitions)
[![Build Status](https://github.com/pytransitions/transitions-gui/actions/workflows/pytest.yml/badge.svg)](https://github.com/pytransitions/transitions-gui/actions?query=workflow%3Apytest)
[![Coverage Status](https://coveralls.io/repos/github/pytransitions/transitions-gui/badge.svg?branch=master)](https://coveralls.io/github/pytransitions/transitions-gui?branch=master)
[![PyPi](https://img.shields.io/pypi/v/transitions-gui.svg)](https://pypi.org/project/transitions-gui)
[![Copr](https://img.shields.io/badge/dynamic/json?color=blue&label=copr&query=builds.latest.source_package.version&url=https%3A%2F%2Fcopr.fedorainfracloud.org%2Fapi_3%2Fpackage%3Fownername%3Daleneum%26projectname%3Dpython-transitions%26packagename%3Dpython-transitions-gui%26with_latest_build%3DTrue)](https://copr.fedorainfracloud.org/coprs/aleneum/python-transitions/)
[![GitHub commits](https://img.shields.io/github/commits-since/pytransitions/transitions-gui/0.1.0.svg)](https://github.com/pytransitions/transitions-gui/compare/0.1.0...master)
[![License](https://img.shields.io/github/license/pytransitions/transitions-gui.svg)](LICENSE)

An extension for the [transitions](https://github.com/pytransitions/transitions) state machine package.
`transitions-gui` uses [tornado](https://www.tornadoweb.org) as a web server and [cytoscape](http://js.cytoscape.org) for graph drawing and manipulation. For information about the javascript workflow head to [frontend](./frontend).
The server (including the state machine) and client (your web browser) communicate via [WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API).

***
**Feedback wanted**: Things do not work out of the box? You are not a big fan of the chosen icons, colours, layouts or styles? Now is the time to speak up and file a [new issue](https://github.com/aleneum/transitions-gui/issues/new).
***

## Installation

Install `transitions-gui` from [PyPI](https://pypi.org/project/transitions-gui/)

```bash
pip install transitions-gui
```

or clone the GitHub repo

```bash
# clone the repository
git clone https://github.com/pytransitions/transitions-gui.git
cd transitions-gui
# install transitions-gui and all dependencies
python setup.py install
```

## Quickstart

Let's begin by creating a simple circular state machine.
Running `python examples/simple.py` will execute the following code:

```python
from transitions_gui import WebMachine
import time

states = ['A', 'B', 'C', 'D', 'E', 'F']
# initializing the machine will also start the server (default port is 8080)
machine = WebMachine(states=states, initial='A', name="Simple Machine",
                     ordered_transitions=True,
                     ignore_invalid_triggers=True,
                     auto_transitions=False)

try:
    while True:
        time.sleep(5)
        machine.next_state()
except KeyboardInterrupt:  # Ctrl + C will shutdown the machine
    machine.stop_server()
```

This will create a simple transitions state machine 'ordered' (as in circular) transitions. The name of the machine will be *Simple Machine* and it will act as its own model which is the default behaviour. The initial state is state *A* and every 5 seconds, the state will be changed. Next, open your favourite yet up-to-date web browser and head to [localhost:8080](http://localhost:8080). You should see something similar to this:
![initial view](doc/img/initial-view.png)

The GUI is rather simplistic and contains only two buttons which you can see on the top left:

* ![pencil](doc/img/pencil.png) - toggles between *Event Mode* and *Edit Mode*
* ![save](doc/img/save.png) - saves the current layout

### Event Mode

The GUI always starts in *Event Mode* which is represented by the pencil's *white* background. In this mode, the graph can be moved around by clicking and dragging but nodes cannot be moved individually. Clicking an edge/transition in *Event Mode* will dispatch the related trigger to the machine. Give it a try! Clicking any edge should trigger an instant state change. Since all edges trigger the `next_state` event it does not matter which edge you click here.

### Edit Mode

Now let's rearrange some state nodes, shall we? Click the pencil symbol to switch to *Edit Mode* (the pencil's background changes its background) and start dragging that nodes like this:

![](doc/img/edit-view.png)

In *Edit Mode* clicking edges will not trigger an event. However, the machine's model state will be updated regardlessly.
When you are done, switch back to *Event Mode*. Or don't. The mode does not matter for the next step. We will save that layout for the next time we want to run our state machine. Clicking the save button (<img src="transitions_gui/static/img/save.svg" height="18" />) will store the nodes' current positions in the browser's local storage. Layouts are stored by their name. If you plan to use `transitions-gui` with multiple state machines, it is recommended to make them distinguishable by name. Now reload your browser tab. Your node arangement should be recreated.
Dragging nodes around will not alter the saved layout unless you save it again.

### About layouts

When a transition state machine configuration is sent to the browser, the browser will determine the layout based on the following priority list:

* value of the passed URL argument `layout`
* layout stored in the browsers local storage
* default layout
  - the machine contains *nested states* -> `dagre`
  - otherwise -> `concentric`

`transitions-gui` might not choose the right layout for your graph right away. By passing different layout values, you can check which arrangement suits your needs the best. Additionally, you can 'reset' the layout if you want your graph to be automatically arranged again. When `layout=<value>` is passed, the manually stored arrangement is ignored. Check the simple machine with an improved version of the CoSE arangement by opening the GUI with [localhost:8080?layout=bilkent](http://localhost:8080?layout=bilkent). This should look like this:

![bilkent](doc/img/load-layout.png)

The currently supported layout values are:

* dagre ([src](https://github.com/cytoscape/cytoscape.js-dagre))
* concentric ([src](http://js.cytoscape.org/#layouts/concentric))
* bilkent ([src](https://github.com/cytoscape/cytoscape.js-cose-bilkent))

This functionality is provided by [cytoscape.js](http://js.cytoscape.org/). If you think `transitions-gui` should support more layouts, feel free to open an issue to propose your favourite layout.

### Show more details

By default, only states and edges are shown.
If you want to annotate `conditions` and `enter/exit` callbacks as well you can pass `details=true` as an URL argument like this:
[localhost:8080?details=true](http://localhost:8080?details=true).
This graph (does not make much sense and) has been generated by `examples/process.py`.
You might remember that graph from transitions' documentation.

![](doc/img/example-graph.png)

### Custom styling

If you want to adjust more than just the position of nodes, you can pass CSS styling information to `WebMachine` via `graph_css`.
This will be forwarded to cytoscape.
A styling item contains a `selector` and a `css` field.

```python
import time

from transitions_gui import WebMachine

# just a simple state machine setup
states = ["Red", "Yellow", "Green"]
transitions = [
    ["tick", "Red", "Green"],
    ["tick", "Green", "Yellow"],
    ["tick", "Yellow", "Red"],
    ["reset", "*", "Red"]
]

# Check https://js.cytoscape.org/#selectors and https://js.cytoscape.org/#style for more options
styling = [
    {"selector": 'node[id = "Green"]',  # state names are equal to node IDs
     "css": {"font-size": 28, "color": "white", "background-color": "darkgreen"}},
    {"selector": 'node[id = "Red"]',
     "css": {"shape": "ellipse", "color": "darkred"}},
    {"selector": 'node[id != "Green"]',  # select all nodes EXCEPT green
     "css": {"border-style": "dotted"}},
    {"selector": "edge",  # select all edges
     "css": {"font-size": 12, "text-margin-y": -12, "text-background-opacity": 0}},
    {"selector": 'edge[source = "Red"][target = "Green"]',  # select all edges from Red to Green
     "css": {"line-gradient-stop-colors": "red yellow black", "line-fill": "linear-gradient"}},
    {"selector": 'edge[label = "reset"]',  # transition triggers map to edge labels (without conditions)
     "css": {"line-style": "dotted", "target-arrow-shape": "triangle-tee"}}
]

machine = WebMachine(
    states=states,
    transitions=transitions,
    initial="Red",
    name="Traffic Machine",
    ignore_invalid_triggers=True,
    auto_transitions=False,
    graph_css=styling,
)

try:
    while True:
        time.sleep(5)
        machine.tick()
except KeyboardInterrupt:  # Ctrl + C will shutdown the machine
    machine.stop_server()
```

To get a better of what you can adjust, have a look at the cytoscape documentation, especially the sections [selectors](https://js.cytoscape.org/#selectors) and [style](https://js.cytoscape.org/#style). The example above should look like this:

![](doc/img/example-styling.png)


### NestedWebMachine

In case you want to use hierarchical machines, you need to use `NestedWebMachine` instead of `WebMachine`.
See for instance `examples/hsm.py` or `examples/parallel.py`.

HSM is a slightly tweaked version of the `transitions` example ...

![](doc/img/hsm.png)

... and `parallel.py` -- as the name suggests -- makes use of parallel states:

![](doc/img/parallel.png)

By the way, the orientation of the dashed line will change when the parallel state's height is larger than its width.
This is an experimental solution and might change in the future.


## I have a [bug report/issue/question]...

For bug reports and other issues, please open an issue on GitHub.



================================================
FILE: examples/hsm.py
================================================
import sys
import time
from os.path import join, realpath, dirname
import logging
from transitions.extensions.states import Timeout, Tags, add_state_features

sys.path.append(join(dirname(realpath(__file__)), '..'))

from transitions_gui import NestedWebMachine  # noqa


@add_state_features(Timeout, Tags)
class MyNestedWebMachine(NestedWebMachine):
    pass


logging.basicConfig(level=logging.INFO)


states = [{'name': 'caffeinated', 'on_enter': 'do_x', 'initial': 'dithering',
           'children': ['dithering', 'running'], 'transitions': [['drink', 'dithering', '=']]},
          {'name': 'standing', 'on_enter': ['do_x', 'do_y'], 'on_exit': 'do_z'},
          {'name': 'walking', 'tags': ['accepted', 'pending'], 'timeout': 5, 'on_timeout': 'do_z'}]

transitions = [
    ['walk', 'standing', 'walking'],
    ['go', 'standing', 'walking'],
    ['stop', 'walking', 'standing'],
    {'trigger': 'drink', 'source': '*', 'dest': 'caffeinated',
     'conditions': 'is_hot', 'unless': 'is_too_hot'},
    ['walk', 'caffeinated_dithering', 'caffeinated_running'],
    ['relax', 'caffeinated', 'standing'],
    ['sip', 'standing', 'caffeinated']
]


class Model:

    def is_hot(self):
        return True

    def is_too_hot(self):
        return False

    def do_x(self):
        pass


machine = MyNestedWebMachine(Model(), states=states, transitions=transitions, initial='new',
                             name="Mood Matrix",
                             ignore_invalid_triggers=True,
                             auto_transitions=False)

try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:  # Ctrl + C will shutdown the machine
    machine.stop_server()



================================================
FILE: examples/multiple.py
================================================
import sys
import time
from os.path import join, realpath, dirname
import logging
import random

sys.path.append(join(dirname(realpath(__file__)), ".."))

from transitions_gui import WebMachine  # noqa

logging.basicConfig(level=logging.INFO)


class Agent:
    def __init__(self, name=None):
        if name is not None:
            self.name = name


class Soldier(Agent):
    pass


class Building(Agent):
    pass


agent_css = [
    {"selector": ".__main__Agent", "style": {"background-color": "DarkGray"}},
    {"selector": ".__main__Soldier", "style": {"background-color": "CadetBlue"}},
    {"selector": ".SgtBloom", "style": {"background-color": "FireBrick"}},
]

environment_css = [
    {"selector": ".__main__Building", "style": {"background-color": "DarkOrange"}},
    {"selector": ".Bunker", "style": {"background-color": "DarkGreen"}},
]

agent_states = ["Idle", "Patrol", "Chasing", "Searching"]
agent_transitions = [
    ["detect", ["Patrol", "Searching"], "Chasing"],
    ["lost", "Chasing", "Searching"],
    ["give_up", "Searching", "Patrol"],
    ["break", "Patrol", "Idle"],
    ["patrol", "Idle", "Patrol"],
]
agents = [Agent(), Soldier(), Soldier("SgtBloom")]

agent_machine = WebMachine(
    model=agents,
    states=agent_states,
    transitions=agent_transitions,
    initial="Idle",
    name="Agents",
    ignore_invalid_triggers=True,
    auto_transitions=False,
    graph_css=agent_css,
    port=8080,
)

environment_states = ["Locked", "Unlocked", "Open"]
environment_transitions = [
    ["unlock", "Locked", "Unlocked"],
    ["lock", "Unlocked", "Locked"],
    ["open", "Unlocked", "Open"],
    ["close", "Open", "Unlocked"],
]
buildings = [Building(), Building("Bunker")]

environment_machine = WebMachine(
    model=buildings,
    states=environment_states,
    transitions=environment_transitions,
    initial="Locked",
    name="Environment",
    ignore_invalid_triggers=True,
    auto_transitions=False,
    graph_css=environment_css,
    port=8081,
)

try:
    while True:
        for model in agents:
            time.sleep(1)
            next_action = random.choice(agent_transitions)
            model.trigger(next_action[0])
        for model in buildings:
            time.sleep(1)
            next_action = random.choice(environment_transitions)
            model.trigger(next_action[0])

except KeyboardInterrupt:  # Ctrl + C will shutdown the machine
    environment_machine.stop_server()
    agent_machine.stop_server()



================================================
FILE: examples/parallel.py
================================================
import sys
import time
from os.path import join, realpath, dirname
import logging

sys.path.append(join(dirname(realpath(__file__)), '..'))

from transitions_gui import NestedWebMachine # noqa


logging.basicConfig(level=logging.INFO)


states = [{'name': 'style',
           'parallel': [
               {
                   'name': 'numbers',
                   'children': ['one', 'two', 'three'],
                   'transitions': [['inc', 'one', 'two'], ['inc', 'two', 'three']],
                   'initial': 'one'
               },
               {
                   'name': 'greek',
                   'children': ['alpha', 'beta', 'gamma'],
                   'transitions': [['inc', 'alpha', 'beta'], ['inc', 'beta', 'gamma']],
                   'initial': 'alpha'
               }]
           }, 'preparing']

transitions = [['inc', 'preparing', 'style'],
               ['inc', 'style', 'preparing']]

machine = NestedWebMachine(states=states, transitions=transitions, initial='preparing',
                           name="Label Machine",
                           ignore_invalid_triggers=True,
                           auto_transitions=False)

try:
    while True:
        time.sleep(5)
        machine.inc()
except KeyboardInterrupt:  # Ctrl + C will shutdown the machine
    machine.stop_server()



================================================
FILE: examples/process.py
================================================
import sys
import time
from os.path import join, realpath, dirname
import logging
from transitions.extensions.states import Timeout, Tags, add_state_features

sys.path.append(join(dirname(realpath(__file__)), '..'))

from transitions_gui import WebMachine  # noqa


@add_state_features(Timeout, Tags)
class CustomMachine(WebMachine):
    pass


logging.basicConfig(level=logging.INFO)

states = ['new', 'approved', 'ready', 'finished', 'provisioned',
          {'name': 'failed', 'on_enter': 'notify', 'on_exit': 'reset',
           'tags': ['error', 'urgent'], 'timeout': 10, 'on_timeout': 'shutdown'},
          'in_iv', 'initializing', 'booting', 'os_ready', {'name': 'testing', 'on_exit': 'create_report'},
          'provisioning']

transitions = [{'trigger': 'approve', 'source': ['new', 'testing'], 'dest':'approved',
                'conditions': 'is_valid', 'unless': 'abort_triggered'},
               ['fail', '*', 'failed'],
               ['add_to_iv', ['approved', 'failed'], 'in_iv'],
               ['create', ['failed', 'in_iv'], 'initializing'],
               ['init', 'in_iv', 'initializing'],
               ['finish', 'approved', 'finished'],
               ['boot', ['booting', 'initializing'], 'booting'],
               ['ready', ['booting', 'initializing'], 'os_ready'],
               ['run_checks', ['failed', 'os_ready'], 'testing'],
               ['provision', ['os_ready', 'failed'], 'provisioning'],
               ['provisioning_done', 'provisioning', 'os_ready']]


class Model:

    def shutdown(self):
        pass

    def create_report(self):
        pass

    def notify(self):
        pass

    def reset(self):
        pass

    def is_valid(self):
        return True

    def abort_triggered(self):
        return False


machine = CustomMachine(Model(), states=states, transitions=transitions, initial='new',
                     name="System State",
                     ignore_invalid_triggers=True,
                     auto_transitions=False)

try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:  # Ctrl + C will shutdown the machine
    machine.stop_server()



================================================
FILE: examples/simple.py
================================================
import sys
import time
from os.path import join, realpath, dirname
import logging

sys.path.append(join(dirname(realpath(__file__)), ".."))

from transitions_gui import WebMachine  # noqa

logging.basicConfig(level=logging.INFO)

states = ["A", "B", "C", "D", "E", "F"]
machine = WebMachine(
    states=states,
    initial="A",
    name="Simple Machine",
    ordered_transitions=True,
    ignore_invalid_triggers=True,
    auto_transitions=False,
)

try:
    while True:
        time.sleep(5)
        machine.next_state()
except KeyboardInterrupt:  # Ctrl + C will shutdown the machine
    machine.stop_server()



================================================
FILE: examples/styling.py
================================================
import sys
import time
from os.path import join, realpath, dirname
import logging

sys.path.append(join(dirname(realpath(__file__)), ".."))

from transitions_gui import WebMachine

logging.basicConfig(level=logging.INFO)

# just a simple state machine setup
states = ["Red", "Yellow", "Green"]
transitions = [
    ["tick", "Red", "Green"],
    ["tick", "Green", "Yellow"],
    ["tick", "Yellow", "Red"],
    ["reset", "*", "Red"]
]

# Check https://js.cytoscape.org/#selectors and https://js.cytoscape.org/#style for more options
styling = [
    {"selector": 'node[id = "Green"]',  # state names are equal to node IDs
     "css": {"font-size": 28, "color": "white", "background-color": "darkgreen"}},
    {"selector": 'node[id = "Red"]',
     "css": {"shape": "ellipse", "color": "darkred"}},
    {"selector": 'node[id != "Green"]',  # select all nodes EXCEPT green
     "css": {"border-style": "dotted"}},
    {"selector": "edge",  # select all edges
     "css": {"font-size": 12, "text-margin-y": -12, "text-background-opacity": 0}},
    {"selector": 'edge[source = "Red"][target = "Green"]',  # select all edges from Red to Green
     "css": {"line-gradient-stop-colors": "red yellow black", "line-fill": "linear-gradient"}},
    {"selector": 'edge[label = "reset"]',  # transition triggers map to edge labels (without conditions)
     "css": {"line-style": "dotted", "target-arrow-shape": "triangle-tee"}}
]

machine = WebMachine(
    states=states,
    transitions=transitions,
    initial="Red",
    name="Traffic Machine",
    ignore_invalid_triggers=True,
    auto_transitions=False,
    graph_css=styling,
)

try:
    while True:
        time.sleep(5)
        machine.tick()
except KeyboardInterrupt:  # Ctrl + C will shutdown the machine
    machine.stop_server()
