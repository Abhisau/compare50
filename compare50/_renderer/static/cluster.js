var radius = 10;

var svg = d3.select("svg"),
    width = +svg.attr("width"),
    height = +svg.attr("height");

var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(function(d) { return d.id; }))
    .force("charge", d3.forceManyBody().strength(-200).distanceMax(50).distanceMin(10))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => radius * 2));

var g_link = svg.append("g").attr("class", "links");

var g_node = svg.append("g").attr("class", "nodes");

function ticked(links, nodes) {
  nodes
      .attr("cx", function(d) { return d.x = Math.max(radius, Math.min(width - radius, d.x)); })
      .attr("cy", function(d) { return d.y = Math.max(radius, Math.min(height - radius, d.y)); });

  links
      .attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });
};

function dragstarted(d) {
  if (!d3.event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}

function dragged(d) {
  d.fx = d3.event.x;
  d.fy = d3.event.y;
}

function dragended(d) {
  if (!d3.event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}

function set_groups(link_data, node_data) {
  // create a map from node_id to node
  let node_map = {};
  node_data.forEach(d => {
    d.group = null;
    node_map[d.id] = d;
  });

  // create a map from node.id to directly connected node.ids
  let link_map = {};
  link_data.forEach(d => {
    if (d.source.id in link_map) {
      link_map[d.source.id].push(d.target.id);
    } else {
      link_map[d.source.id] = [d.target.id];
    }

    if (d.target.id in link_map) {
      link_map[d.target.id].push(d.source.id);
    } else {
      link_map[d.target.id] = [d.source.id];
    }
  })

  let group_id = 0;
  let visited = new Set();
  let unseen = new Set(Object.keys(node_map));

  // visit all nodes
  while (unseen.size > 0) {
    // start with an unseen node
    let node_id = unseen.values().next().value;
    unseen.delete(node_id);

    // DFS for all reachable nodes, start with all directly reachable
    let stack = [node_id];
    while (stack.length > 0) {
      // take top node on stack
      let cur_node_id = stack.pop();

      // visit it, give it a group
      visited.add(cur_node_id);
      node_map[cur_node_id].group = group_id;

      // add all directly reachable (and unvisited nodes) to stack
      let directly_reachable = link_map[cur_node_id].filter(id => unseen.has(id));
      stack = stack.concat(directly_reachable);

      // remove all directly reachable elements from unseen
      directly_reachable.forEach(id => unseen.delete(id));
    }

    group_id++;
  }

  node_data.forEach(d => d.group = node_map[d.id].group);

  // update color selecter and number of groups
  n_groups = Math.max.apply(0, node_data.map(node => +node.group));
  color = d3.scaleSequential().domain([0, n_groups + 1]).interpolator(d3.interpolateRainbow);
}

function cutoff(n) {
  let link_data = graph.links.filter(d => (+d.value) <= n);
  let node_ids = new Set(link_data.map(d => d.source.id).concat(link_data.map(d => d.target.id)));
  let node_data = graph.nodes.filter(d => node_ids.has(d.id));

  update(link_data, node_data);
}

function update(link_data, node_data) {
  var links = g_link.selectAll("line").data(link_data);

  links.enter().append("line")
      .attr("stroke-width", 2);

  links.exit().remove();

  var nodes = g_node.selectAll("circle").data(node_data);

  nodes.enter().append("circle")
    .attr("r", radius)
    .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended))
    .on("click", (d) => console.log(d.id))
    .append("title").text(d => d.id);

  nodes.exit().remove();

  let all_links = g_link.selectAll("line");
  let all_nodes = g_node.selectAll("circle");

  // don't swap simulation.nodes and simulation.force
  simulation
      .nodes(node_data)
      .on("tick", () => ticked(all_links, all_nodes));

  simulation.force("link")
      .links(link_data)
      .distance(d => (+d.value) * 10);

  simulation.alphaTarget(0.3).restart();
  setTimeout(() => simulation.alphaTarget(0).restart(), 1000);

  // Don't move this up, this needs to be after simulation.force!!!
  set_groups(link_data, node_data);
  all_nodes.style("fill", d => color(+d.group))
}

update(graph.links, graph.nodes)