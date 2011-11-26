var w = 960,
    h = 500,
    fill = d3.scale.linear()
      .domain([-1,0,5,10,Infinity])
      .range(["white", "green", "yellow", "red", "red"]);

var vis = d3.select("#chart").append("svg:svg")
    .attr("width", w)
    .attr("height", h);

d3.json("t.json", function(json) {
  // create nodes and node index
  var ix = {null:0};
  var nodes = [{"content": "(original article)", "ups": 25, "downs": -1, "published": json.results[0].published-1.0}];
  var i = 1;
  for (r in json.results) {
      n = json.results[r];
      nodes.push(n);
      ix[n.id] = i;
      i++;
  }

  // create links
  var links = [];
  for (i in json.results) {
      var id = json.results[i].id;
      var p_id = json.results[i].parent_id;
      links.push({"source":ix[p_id], "target":ix[id], "weight":1});
  }

  var link_distance = function(link) {
      d = (link.target.published - link.source.published);
      return 1.0 + Math.log(1.0 + Math.abs(d/1000.0));
  }

  var force = d3.layout.force()
      .charge(-25)
      .friction(.9)
      .linkDistance(link_distance)
      .nodes(nodes)
      .links(links)
      .size([w, h])
      .start();

  var link = vis.selectAll("line.link")
      .data(links)
    .enter().append("svg:line")
      .attr("class", "link")
      .style("stroke-width", function(d) { return Math.sqrt(d.value); })
      .attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });

  var node = vis.selectAll("circle.node")
      .data(nodes)
    .enter().append("svg:circle")
      .attr("class", "node")
      .attr("cx", function(d) { return d.x; })
      .attr("cy", function(d) { return d.y; })
      .attr("r", function(d) { return d.ups+1; })
      .style("fill", function(d) { return fill(d.downs); })
      .call(force.drag);

  node.append("svg:title")
      .text(function(d) { return d.content; });

  force.on("tick", function() {
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node.attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
  });
});
