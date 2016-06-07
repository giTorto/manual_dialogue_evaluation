
/**
 * Created by gt on 03/06/16.
 */

var nextreply =0;
var actualdid = '';
var dialogues = [];
var mydiagram= '';
var keys = [];
function mayWorkFor(node1, node2) {
      if (!(node1 instanceof go.Node)) return false;  // must be a Node
      if (node1 === node2) return false;  // cannot work for yourself
      if (node2.isInTreeOf(node1)) return false;  // cannot work for someone who works for you
      return true;
    }

//this will be a post request
function send_graph_to_server(text, filename){
    //var save_file = require('file-save');
    //save_file.saveAs(text,filename)
    $.ajax({
    url: '/Dialogue_to_graph/dialogues/save-json/',
    type: 'POST',
    contentType: 'application/json; charset=utf-8',
    data: text,
    dataType: 'text',
    success: function(result) {
    }
});
    console.log(text)
}

function storedialogue_startnewone(actualdid){
    ( function($) {
            $("#next_reply").text('Next Reply')
    } ) ( jQuery );

    var modelAsText = JSON.parse(myDiagram.model.toJson());

    modelAsText.did = dialogues[actualdid].key;
    send_graph_to_server(JSON.stringify(modelAsText));
    nextreply = 0;
    create_starting_graph()

}

function get_new_dialogues(){
    $.getJSON("/Dialogue_to_graph/dialogues/get", function(json) {
    //console.log(json); // this will show the info it in firebug console
    var data = {};
    for(i=0; i< json.length;i++){
        did = json[i]['fields']['did'];
        if (!(did in data)){
            data[did] = []
        }
        data[did].push(json[i]['fields']);
    }
    var chiavi = Object.keys(data);
    console.log(chiavi);

    // load each dialogue
    var skip = false;

    chiavi.forEach(function(did){
        skip = false;
        Object.keys(dialogues).forEach(function(dia_ind){
            console.log(dialogues[dia_ind]['key']);
            if (dialogues[dia_ind]['key']==did)
                skip=true;
        });
        console.log(skip)
        if (skip == true)
            return;

        var array = data[did];
        dialogues.push({
            key: did,
            value: array.sort(compare)
        });
    });

    keys = Object.keys(dialogues);

    var final_keys = [];
    for(i=0;i<keys.length;i++){
        if (keys[i]>actualdid)
            final_keys.push(keys[i])
    }
    keys = final_keys
    });
}


function create_starting_graph(){
    var $ = go.GraphObject.make;

    actualdid = keys.shift();
    if (keys.length==0){
        get_new_dialogues();
        if (keys.length==0)
            get_new_dialogues()
    }
    //console.log(actualdid);
    var array = dialogues[actualdid].value;
    console.log(dialogues[actualdid]);
    var new_model = new Array(2);

    for(i=0; i < array.length && i<2; i++) {
        var new_node =from_reply_to_element_model(array[i]);
        if (i==0)
            parent=new_node.key;
        else
            new_node['parent'] = parent;
        new_model[i] = new_node;
        nextreply=i+1
    }
    var model = $(go.TreeModel);
    model.nodeDataArray = new_model;
    myDiagram.model = model;
}

function createNewNode() {
    var array = dialogues[actualdid].value;
    if (nextreply==array.length){
        storedialogue_startnewone(actualdid);
        return
    }
    var new_node =from_reply_to_element_model(array[nextreply]);
    nextreply +=1;

    myDiagram.startTransaction("add reply");
    var nextkey = (myDiagram.model.nodeDataArray.length + 1).toString();
    var newemp = { key: nextkey, name: "(new person)", content: "" };
    myDiagram.model.addNodeData(new_node);
    myDiagram.commitTransaction("add reply");
    if (nextreply == array.length){
        ( function($) {
            $("#next_reply").text('Commit Graph Representation')
        } ) ( jQuery );
    }
}

function compare(a,b) {
  if (a.type=='start_discussion')
    return -1;
  else if (b.type=='start_discussion')
    return 1;
  else if (a.time<b.time)
      return -1;
  else if (b.time<a.time)
      return 1;
  else
    return 0;
}

function createDiagram(){


    var $ = go.GraphObject.make;
    myDiagram =
        $(go.Diagram, "myDiagramDiv",  {
            initialContentAlignment: go.Spot.Center, // center Diagram contents
            maxSelectionCount: 1, // users can select only one part at a time
            validCycle: go.Diagram.CycleDestinationTree, // make sure users can only create trees
            layout:
            $(go.TreeLayout,
              {
                treeStyle: go.TreeLayout.StyleLastParents,
                arrangement: go.TreeLayout.ArrangementHorizontal,
                // properties for most of the tree:
                angle: 90,
                layerSpacing: 35,
                // properties for the "last parents":
                alternateAngle: 90,
                alternateLayerSpacing: 35,
                alternateAlignment: go.TreeLayout.AlignmentBus,
                alternateNodeSpacing: 20
              })
    });
    // define a simple Node template
    myDiagram.nodeTemplate =
      $(go.Node, "Auto",
        { // handle dragging a Node onto a Node to (maybe) change the reporting relationship
          mouseDragEnter: function (e, node, prev) {
            var diagram = node.diagram;
            var selnode = diagram.selection.first();
            if (!mayWorkFor(selnode, node)) return;
            var shape = node.findObject("SHAPE");
            if (shape) {
              shape._prevFill = shape.fill;  // remember the original brush
              shape.fill = "darkred";
            }
          },
          mouseDragLeave: function (e, node, next) {
            var shape = node.findObject("SHAPE");
            if (shape && shape._prevFill) {
              shape.fill = shape._prevFill;  // restore the original brush
            }
          },
          mouseDrop: function (e, node) {
            var diagram = node.diagram;
            var selnode = diagram.selection.first();  // assume just one Node in selection
            if (mayWorkFor(selnode, node)) {
              // find any existing link into the selected node
              var link = selnode.findTreeParentLink();
              if (link !== null) {  // reconnect any existing link
                link.fromNode = node;
              } else {  // else create a new link
                diagram.toolManager.linkingTool.insertLink(node, node.port, selnode, selnode.port);
              }
            }
          }
        },
          new go.Binding("layerName", "isSelected", function(sel) { return sel ? "Foreground" : ""; }).ofObject(),
        // define the node's outer shape
        $(go.Shape, "Rectangle",
          {
            name: "SHAPE", fill: "black", stroke: null,
            // set the port properties:
            portId: "", fromLinkable: true, toLinkable: true, cursor: "arrow"
          }),
        $(go.Panel, "Horizontal",
          // define the panel where the text will appear
          $(go.Panel, "Table",
            {
              maxSize: new go.Size(250, 900),
              margin: new go.Margin(6, 10, 0, 3),
              defaultAlignment: go.Spot.Left
            },
            $(go.RowColumnDefinition, { column: 1, width: 2 }),

        // the entire node will have a light-blue background
        $(go.TextBlock,
          "User A",  // the initial value for TextBlock.text
            // some room around the text, a larger font, and a white stroke:
            { stroke: "white", font: "bold 16px sans-serif ",editable:false,row:0,column:0,columnSpan: 5},
            // TextBlock.text is data bound to the "name" attribute of the model data
            new go.Binding("text", "name")),
          $(go.TextBlock, 'Default Text',
              {stroke: "white", font: "12px sans-serif",isMultiline: true,editable:false,row:1,column:0,columnSpan:5 },
              new go.Binding("text",'content'))
      )));

    myDiagram.linkTemplate =
      $(go.Link, go.Link.Orthogonal,
        { corner: 5, relinkableFrom: true, relinkableTo: true },
        $(go.Shape, { strokeWidth: 4, stroke: "#00a4a4" }));
}

function from_reply_to_element_model(reply){
    //console.log(reply);
    var final_key = '';
    console.log(reply.pid);
    if (reply.pid == '')
        final_key +='0';
    var key = reply.pid.toString() +reply.cid.toString()+reply.time.toString()+final_key;
    //console.log(key);
    object = {
        'key':key,
        'name':reply.user,
        'content':reply.content,
        'pid':reply.pid,
        'cid':reply.cid,
        'time':reply.time
    };
    //console.log(object);

    return object;
}


// this become a get request
$.getJSON("/Dialogue_to_graph/dialogues/get", function(json) {
    //console.log(json); // this will show the info it in firebug console
    var data = {};
    for(i=0; i< json.length;i++){
        did = json[i]['fields']['did'];
        if (!(did in data)){
            data[did] = []
        }
        data[did].push(json[i]['fields']);
    }
    dialogues = [];
    keys = Object.keys(data);
    // load each dialogue
    keys.forEach(function(did){
        array = data[did];
        dialogues.push({
            key: did,
            value: array.sort(compare)
        });
    });
    keys = Object.keys(dialogues);

    // console.log(dialogues);
    // console.log(dialogues.length);
    //var ol = $('<ol></ol>');
    //$('#nav').append(ol);
    //ol.attr('id','did_list');
    ( function($) {
        $("#next_reply").click(createNewNode);

    } ) ( jQuery );

    // define properties of graph
    createDiagram();
    var $ = go.GraphObject.make;

    actualdid = keys.shift();
    var new_model = new Array(2);
    var parent = '';
    var array = dialogues[actualdid].value;
    //console.log(array);
    console.log(dialogues[actualdid]);
    for(i=0; i < array.length && i<2; i++) {
        var new_node =from_reply_to_element_model(array[i]);
        if (i==0)
            parent=new_node.key;
        else
            new_node['parent'] = parent;
        new_model[i] = new_node;
        nextreply=i+1
    }
    //console.log(new_model);
    var model = $(go.TreeModel);
    model.nodeDataArray = new_model;
    myDiagram.model = model;
    //console.log(model.nodeDataArray );
    /*
    keys.forEach(function(did){
        $('#did_list').append('<li>'+did+'</li>')
    })*/

});