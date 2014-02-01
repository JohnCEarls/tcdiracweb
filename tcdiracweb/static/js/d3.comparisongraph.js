
function scatter_graph(header){
    $('a#brand-gene').text(header.gene);
    var margin = {top: 20, right: 20, bottom: 30, left: 50},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;
    var x = d3.scale.linear()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left");
    var svg = d3.select("svg#d3svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    var filename = header["filename-expression"];
    if(use_rank_view){//global set in differencechart.html
        filename = header["filename-rank"]; 
    }
    d3.tsv(filename, function(error, data) {
        if(error){
            console.log(error);
        }
      data.forEach(function(d) {
        d.age = +d[header.age];
        d[header.base]= +d[header.base];
        d[header.comp] = +d[header.comp];
        d[header.base + '-true'] = +d[header.base + '-true'];
        d[header.comp + '-true'] = +d[header.comp + '-true'];
      });
      x.domain(d3.extent(data, function(d) { return d.age; }));
    //if( !$('#rank-source').is(':checked') ) {
    if (!use_rank_view){//global set in differencechart.html
      y.domain([
        d3.min(data, function(d) { return Math.min(d[header.base], d[header.comp]); }),
        d3.max(data, function(d) { return Math.max(d[header.base], d[header.comp]); })
      ]);
    } else {

      y.domain([$('div#gene-choosers').children().length, 0]);
    }

      svg.datum(data);
      svg.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0," + height + ")")
          .call(xAxis);

      svg.append("g")
          .attr("class", "y axis")
          .call(yAxis)
        .append("text")
          .attr("transform", "rotate(-90)")
          .attr("y", 6)
          .attr("dy", ".71em")
          .style("text-anchor", "end")
          .style("fill", "black")
          .style("stroke", "black");

        d3.selectAll("path.domain")
            .style('fill', 'none')
            .style('stroke', '#000')
            .style('shape-rendering', 'crispEdges')
            .style('stroke-width', '1.5px')
            ;

        svg.selectAll("circle")
            .data(data)
            .enter().append("svg:circle")
            .attr("cx", function(d) { return x(d[header.age]); })
            .attr("cy", function(d) { 
                if( isNaN(d[header.base +'-true']) ){
                    return -1000;//off svg
                } else {
                return y(d[header.base +'-true']); }})
            .attr("r", 4.5)
            .style("fill", '#fff')
            .style("stroke", '#000');
        
        svg.selectAll("path.compare")
            .data(data)
            .enter().append("path")
                .attr("transform", 
                    function(d) { 
                        if( isNaN(d[header.comp +'-true']) ){
                            return "translate(-1000,-1000)";
                        } else {
                    return "translate(" + 
                        x(d[header.age]) + "," + y(d[header.comp]) + ")";} })
                .attr("d", d3.svg.symbol()
                    .type( "triangle-down" )
                )
            .style("fill", 'rgb(145,207,96)')
            .style("stroke", '#000')
            .style("opacity", ".5")
            ;
    //addSave();
    });}    


function comparison_graph(header){
    return scatter_graph(header);
    $('a#brand-gene').text(header.gene);
    var margin = {top: 20, right: 20, bottom: 30, left: 50},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;
    var x = d3.scale.linear()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left");
    var line = d3.svg.area()
        .interpolate("basis")
        .x(function(d) { return x(d[header.age]); })
        .y(function(d) { return y(d[header.base]); });

    var area = d3.svg.area()
        .interpolate("basis")
        .x(function(d) { return x(d[header.age]); })
        .y1(function(d) { return y(d[header.base]); });

    //var svg = d3.select("body").append("svg")
    //var svg = d3.select("div#svg-holder").append("svg")
        var svg = d3.select("svg#d3svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    var filename = header["filename-expression"];
    if(use_rank_view){//global set in differencechart.html
        filename = header["filename-rank"]; 
    }
    d3.tsv(filename, function(error, data) {
        if(error){
            console.log(error);
        }
      data.forEach(function(d) {
        d.age = +d[header.age];
        d[header.base]= +d[header.base];
        d[header.comp] = +d[header.comp];
      });

      x.domain(d3.extent(data, function(d) { return d.age; }));


    //if( !$('#rank-source').is(':checked') ) {
    if (!use_rank_view){//global set in differencechart.html
      y.domain([
        d3.min(data, function(d) { return Math.min(d[header.base], d[header.comp]); }),
        d3.max(data, function(d) { return Math.max(d[header.base], d[header.comp]); })
      ]);
    } else {

      y.domain([$('div#gene-choosers').children().length, 0]);
    }

      svg.datum(data);

      svg.append("clipPath")
          .attr("id", "clip-below")
        .append("path")
          .attr("d", area.y0(height));

      svg.append("clipPath")
          .attr("id", "clip-above")
        .append("path")
          .attr("d", area.y0(0));

      svg.append("path")
          .attr("class", "area above")
          .attr("clip-path", "url(#clip-above)")
          .attr("d", area.y0(function(d) { return y(d[header.comp]); }));
      svg.append("path")
          .attr("class", "area below")
          .attr("clip-path", "url(#clip-below)")
          .attr("d", area);

      svg.append("path")
          .attr("class", "line")
          .attr("d", line);

      svg.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0," + height + ")")
          .call(xAxis);

      svg.append("g")
          .attr("class", "y axis")
          .call(yAxis)
        .append("text")
          .attr("transform", "rotate(-90)")
          .attr("y", 6)
          .attr("dy", ".71em")
          .style("text-anchor", "end")
          .style("fill", "black")
          .style("stroke", "black");

        d3.selectAll("path.domain")
            .style('fill', 'none')
            .style('stroke', '#000')
            .style('shape-rendering', 'crispEdges')
            .style('stroke-width', '1.5px')
            ;
        //d3.selectAll(".x.axis").style('display','none');
        d3.selectAll('.area.above').style('fill','rgb(252,141,89)');
        d3.selectAll('.area.below').style('fill','rgb(145,207,96)')
        d3.selectAll('.line').style( 'fill', 'none')
              .style('stroke', '#000')
              .style('stroke-width','1.5px');

        svg.selectAll("circle")
            .data(data)
            .enter().append("svg:circle")
            .attr("cx", function(d) { return x(d[header.age]); })
            .attr("cy", function(d) { return y(d[header.base]); })
            .attr("r", 4.5)
            .style("fill", '#fff')
            .style("stroke", '#000');

        svg.selectAll("path.compare")
            .data(data)
            .enter().append("path")
                .attr("transform", 
                    function(d) { 
                    return "translate(" + 
                        x(d[header.age]) + "," + y(d[header.comp]) + ")"; })
                .attr("d", d3.svg.symbol()
                    .type( "triangle-down" )
                )
            .style("fill", 'rgb(145,207,96)')
            .style("stroke", '#000')
            .style("opacity", ".5")
            ;
    //addSave();  
    });}    
