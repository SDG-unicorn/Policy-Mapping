function getColor(txt) {
	switch (txt) {
		case "SDG 1":
			return "#E5243B";
			break;
		case "SDG 2":
			return "#DDA63A";
			break;
		case "SDG 3":
			return "#4C9F38";
			break;
		case "SDG 4":
			return "#C5192D";
			break;
		case "SDG 5":
			return "#FF3A21";
			break;
		case "SDG 6":
			return "#26BDE2";
			break;
		case "SDG 7":
			return "#FCC30B";
			break;
		case "SDG 8":
			return "#A21942";
			break;
		case "SDG 9":
			return "#FD6925";
			break;
		case "SDG 10":
			return "#DD1367";
			break;
		case "SDG 11":
			return "#FD9D24";
			break;
		case "SDG 12":
			return "#BF8B2E";
			break;
		case "SDG 13":
			return "#3F7E44";
			break;
		case "SDG 14":
			return "#0A97D9";
			break;
		case "SDG 15":
			return "#56C02B";
			break;
		case "SDG 16":
			return "#00689D";
			break;
		case "SDG 17":
			return "#19486A";
			break;
		case "Human Development":
			return "#F68D4A";
			break;
		case "Growth Jobs":
			return "#FABE13";
			break;
		case "Green Deal":
			return "#1A6835";
			break;
		case "Governance":
			return "#005C95";
			break;
		case "Digitalisation":
			return "#4D9CD5";
			break;
		case "Migration":
			return "#DE6189";
			break;
		default:
			return "white";
	}
}

function getText(size) {
	var	pol_str = size == 1 ? " Initiative" : " Initiatives";
	return "(" + size + pol_str + ")";
}

function getTspan(text) {
	svg.selectAll("tspan").remove();
	text
		.append("tspan")
		.text(function (d) {
			return d.data.name;
		})
		.style("font-size", "15px")
		.attr("y", -5)
		.attr("y", 0)
		.attr("class", "label-sdg");

  /*text
    .append("tspan")
    .text(function (d) {
      return getText(d.data.size);
    })
    .style("font-size", "11px")
    .attr("x", 0)
    .attr("dy", 20)
    .attr("class", "label-policies");*/
}

var svg = d3.select("#chart"),
	margin = 5,
	diameter = svg.attr("width");

function loadChart(file) {
	var g = svg.append("g").attr("transform", "translate(" + diameter / 2 + "," + diameter / 2 + ")");

	var pack = d3.pack()
		.size([diameter - margin, diameter - margin])
		.padding(25);

	d3.json(file + "?_=" + new Date().getTime() ).then(function (data) {
		root = d3.hierarchy(data)
			.sum(function (d) {
				return d.size;
			})
			.sort(function (a, b) {
				return b.value - a.value;
			});

		var nodes = pack(root).descendants(),
			view;

		var circle = g.selectAll("circle")
			.data(nodes)
			.enter().append("circle")
			.attr("class", function (d) {
				return d.parent ? d.children ? "node" : "node node--leaf" : null;
			})
			.style("fill", function (d) {
				var n = d.data.name;
				return getColor(n) ? getColor(n) : null;
			})
			.style("fill-opacity", 0);

		circle
			.style("fill-opacity", function (d) {
				return d.parent === root ? 1 : 0.2;
				//return 1;
			});

		var text = g.selectAll("text")
			.data(nodes)
			.enter().append("text")
			.style("fill-opacity", 0)
			.style("display", function (d) {
				return d.parent === root ? "inline" : "none";
				//return d.depth === 2 ? "inline" : "none";
			});
		getTspan(text);

		text
			.style("fill-opacity", function (d) {
				return d.parent === root ? 1 : 0;
				//return d.depth === 2 ? 1 : 0;
			});

		var node = g.selectAll("circle,text");

		svg.style("background", "white");

    var node = g.selectAll("circle,text");
    function addCircles(v) {
			var k = diameter / v[2];
			view = v;
			node.attr("transform", function (d) {
				return "translate(" + (d.x - v[0]) * k + "," + (d.y - v[1]) * k + ")";
			});
			circle.attr("r", function (d) {
				return d.r * k;
			});
		}
		addCircles([root.x, root.y, root.r * 2 + margin]);
	}, function (error) {
		throw error;
	});
}

loadChart("json/sdg_bubbles.json");
//loadChart("json/priority_bubbles.json");
//loadChart("json/polprior_bubbles_ref.json");
//loadChart("json/AFGHANISTAN _ Jobs and Peace 05-10-2020 (2)pdf.json");

