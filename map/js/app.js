const WORLD_DATA_URL = 'https://gist.githubusercontent.com/mbostock/4090846/raw/d534aba169207548a8a3d670c9c2cc719ff05c47/world-110m.json'

class App {
    constructor(div) {
        this.div = div
    }

    async fetchData() {
        // using the fetch api to load all the initial data

        // fetching world data for the globe
        let worldDataResponse = await fetch(WORLD_DATA_URL);
        let topo = await worldDataResponse.json();

        // converting topojson to geojson
        // MIGHT WANNA PRERENDER THAT FOR RELEASE
        this.worldData = topojson.feature(topo, topo.objects.countries)

        // loading initial response
        // extracting raster
        this.raster = LOCATIONS["raster"]

        // setting raster information object
        this.rasterInfo = LOCATIONS["information"]
        
        // deriving some constants from the info
        this.dx = this.rasterInfo["dx"]
        this.dy = this.rasterInfo["dy"]

        // JITTER DATA
        this.raster = this.raster.map((e) => {
        	return([
        		[e[0][0] + d3.randomUniform(-this.dx, this.dx)()/2,
        		 e[0][1] + d3.randomUniform(-this.dy, this.dy)()/2],
        		 e[1]
        	])
        })
        
    }

    async initiateEnvironment() {
        // intiating all things that we'll need throughout
        // (and that won't change after fetching data)

        // loading base data
        await this.fetchData()

        // creating graticules
        this.graticule = d3.geoGraticule()
            .step([10, 10]);



    }

    setDimensions() {
        // Setting all the dimensions for the graph

        this.boundingRect = this.div.getBoundingClientRect();
        this.height = this.boundingRect.height;
        this.width = this.boundingRect.width;

        	// derived quantities
        this.center = [this.width / 2, this.height / 2]
        this.dim = [this.width, this.height]

        

    }


    createGraph() {
    	// Defining all needed operators and quantities

    		// defining projection
        this.projection = d3.geoNaturalEarth1().scale(1).rotate(90)
            .fitSize([d3.max(this.dim), d3.min(this.dim)], this.worldData)

        	// defining geoPath generator
        this.geoPath = d3.geoPath().projection(this.projection)

        // defining scales

        	// most number of visits of a square
        this.maxVisit = d3.max(this.raster.map((e) => { return e[1] })) 
        
        this.radiusFromVisits = d3.scalePow()
            .domain([0, this.maxVisit])
            .range([0, 2]).exponent(0.2)

        this.opacityFromVisits = d3.scalePow()
            .domain([0, this.maxVisit])
            .range([0, 1]).exponent(0.2)

        // creating circle path constructor
        this.circle = d3.geoCircle()
            .radius((d) => {
                return this.radiusFromVisits(d[1])
            })
            .center((d) => {
                return d[0]
            })

        // plotting the data

        	// create svg container
        this.svg = d3.select(this.div).append("svg")
            .attr("height", d3.min(this.dim))
            .attr("width", d3.max(this.dim))
        
        	// if height bigger then width, then rotate to display sideways
        if( this.height > this.width) {
            this.svg
            .attr("transform", "translate(" + (this.width - this.height
            	)/2 +", " + (this.height - this.width
            	)/2 + ") rotate(90)")
        }
        
        	// plot graticules
        this.svg.append("path")
            .attr("class", "graticule")
            .datum(this.graticule)
            .attr("d", this.geoPath)
            .style("fill", "none")
            .style("stroke", "#ccc");

        	// plot globe
        this.svg.selectAll(".segment")
            .data(this.worldData.features)
            .enter().append("path")
            .attr("class", "segment")
            .attr("d", this.geoPath)
            .style("stroke-width", "1px")
            .style("opacity", ".6");

        	// plot raster data
        this.svg.selectAll("circle")
            .data(this.raster)
            .enter().append("path")
            .attr("class", "marker")
            .attr("d", (d) => {
                return this.geoPath(this.circle(d))
            })
            .attr("stroke","red")
            .attr("fill","orangered")
            .attr("opacity", (d) => {
            	return this.opacityFromVisits(d[1])
            })
    }

    async updateData() {
        // updating the data
    }


    handleResize() {
        // handling resize

        	// just redraw the graph with the new dimensions
        this.setDimensions()
        	// remove old graph
        this.svg.remove()
        	// draw new
        this.createGraph()
    }

    addEvents() {
        // adding event handlers

        	// binding this
        this.handleResize = this.handleResize.bind(this)

        	// adding debounced resize handler
        window.addEventListener("resize", _.debounce(this.handleResize, 100))
    }

    async run() {
        // putting it all together
        await this.initiateEnvironment()
        this.setDimensions()
        this.createGraph()
        this.addEvents()
    }
}


// debug 

let container = document.querySelector("div.container")

let app = new App(container)

app.run()