
var graph_row_name = "graphrow";
var graph_area_container_name = "grapharea";
var src_sid_form_id = "srcsid";
var dst_sid_form_id = "dstsid";
var graphid_form_id = "graphid";

function draw_graph(container, graph_data){
    //container: the element to put graph data in
    //graph data: json data from get_graph_data
    //

    // -------------------------------------------------------------------------
  // OPTIONS:

  // http://visjs.org/docs/network/#modules
  // http://visjs.org/docs/network/edges.html#
  // http://visjs.org/docs/network/physics.html#

  var options = {
    edges: {
      arrows: {
        to: {enabled: true, scaleFactor:0.75, type:'arrow'},
        // to: {enabled: false, scaleFactor:0.5, type:'bar'},
        middle: {enabled: false, scaleFactor:1, type:'arrow'},
        from: {enabled: true, scaleFactor:0.3, type:'arrow'}
        // from: {enabled: false, scaleFactor:0.5, type:'arrow'}
      },
      arrowStrikethrough: true,
      chosen: true,
      color: {
      // color:'#848484',
      color:'red',
      highlight:'#848484',
      hover: '#848484',
      inherit: 'from',
      opacity:1.0
      },
      dashes: false,
      font: {
        color: '#343434',
        size: 14, // px
        face: 'arial',
        background: 'none',
        strokeWidth: 2, // px
        strokeColor: '#ffffff',
        align: 'horizontal',
        multi: false,
        vadjust: 0,
        bold: {
          color: '#343434',
          size: 14, // px
          face: 'arial',
          vadjust: 0,
          mod: 'bold'
        },
        ital: {
          color: '#343434',
          size: 14, // px
          face: 'arial',
          vadjust: 0,
          mod: 'italic'
        },
        boldital: {
          color: '#343434',
          size: 14, // px
          face: 'arial',
          vadjust: 0,
          mod: 'bold italic'
        },
        mono: {
          color: '#343434',
          size: 15, // px
          face: 'courier new',
          vadjust: 2,
          mod: ''
        }
      }
    },
    // http://visjs.org/docs/network/physics.html#
    physics: {
      enabled: true,
      barnesHut: {
        gravitationalConstant: -2000,
        centralGravity: 0.3,
        // springLength: 95,
        springLength: 175,
        springConstant: 0.04,
        damping: 0.09,
        avoidOverlap: 0
      },
      forceAtlas2Based: {
        gravitationalConstant: -50,
        centralGravity: 0.01,
        springConstant: 0.08,
        springLength: 100,
        damping: 0.4,
        avoidOverlap: 0
      },
      repulsion: {
        centralGravity: 0.2,
        springLength: 200,
        springConstant: 0.05,
        nodeDistance: 100,
        damping: 0.09
      },
      hierarchicalRepulsion: {
        centralGravity: 0.0,
        springLength: 100,
        springConstant: 0.01,
        nodeDistance: 120,
        damping: 0.09
      },
      maxVelocity: 50,
      minVelocity: 0.1,
      solver: 'barnesHut',
      stabilization: {
        enabled: true,
        iterations: 1000,
        updateInterval: 100,
        onlyDynamicEdges: false,
        fit: true
      },
      timestep: 0.5,
      adaptiveTimestep: true
    },

    //remove the layout entry to see a differet representation
    //layout: {
    //                hierarchical: {
    //                    direction: "LR",
    //                    sortMethod: "directed",
    //                    levelSeparation: 400,
    //                    nodeSpacing: 100, 
    //                    //randomSeed: 6
    //                }
    //            },
    //            interaction: {
    //                hover: true
    //            }
  };

  var network = new vis.Network(container, graph_data, options);
};
  

function do_graph(d){
    var graphid = document.getElementById(graphid_form_id).value;
    var src = document.getElementById(src_sid_form_id).value;
    var dst = document.getElementById(dst_sid_form_id).value;
    
    url = "";

    
    switch(d) {
        case "domainadmins":
            url = "/graph/"+ graphid +"/query/path/da/?format=vis";
            break;
        case "src":
            url = "/graph/"+ graphid +"/query/path?src="+ src +"&format=vis";
            break;
        case "dst":
            url = "/graph/"+ graphid +"/query/path?dst="+ src +"&format=vis";
            break;
        case "path":
            url = "/graph/"+ graphid +"/query/path?dst="+ dst +"&src="+ src +"&format=vis";
            break;
        default:
            console.error("get_graph_data invoked with unknown d");
            throw "get_graph_data invoked with unknown d";
    }
    var json = $.getJSON(url)
    .done(function(data){
        var graph_data = {
            nodes: data.nodes,
            edges: data.edges
        };
        
        var container = document.getElementById(graph_area_container_name);
        draw_graph(container, graph_data);
    });
};

