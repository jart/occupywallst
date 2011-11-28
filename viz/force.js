var w = 1024,
    h = 1024,
    fill = d3.scale.linear()
      .domain([-1,0,5,10,Infinity])
      .range(["white", "green", "yellow", "red", "red"]);

var vis = d3.select("#chart").append("svg:svg")
    .attr("width", w)
    .attr("height", h);

d3.json("t.json", function(json) {
  // create nodes and node index
  var ix = {null:0};
  users = {};
  for (var r in json.results) {
      users[json.results[r].user] = [];
  }

  var nodes = [{"content": "(original article)", "ups": 25, "downs": -1, "published": json.results[0].published-1.0}];
  for (var r in json.results) {
      var n = json.results[r];
      ix[n.id] = nodes.length;
      nodes.push(n);
      users[n.user].push(n.id)
  }

  // create links
  var links = [];
  for (var i in json.results) {
      var id = json.results[i].id;
      var p_id = json.results[i].parent_id;
      links.push({"source":ix[p_id], "target":ix[id], "weight":1});
  }

  // add squares for users
  var user_list = [];
  for (var u in users) {
      user_list.push(u);
  }
  var user = vis.selectAll("circle")
      .data(user_list)
    .enter().append("svg:circle")
      .attr("cx", 10)
      .attr("cy", function(d, i) { return 10*i; });
	    
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
      .style("stroke-width", 1.0)
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
