const canvas = document.getElementById("graphCanvas")
const ctx = canvas.getContext("2d")
// Load real data
data = [
    {x: 1, y: 25},
    {x: 2, y: 28},
    {x: 3, y: 40},
    {x: 4, y: 45},
    {x: 5, y: 48},
    {x: 6, y: 59},
    {x: 7, y: 60},
    {x: 8, y: 75},
    {x: 9, y: 86},
    {x: 10, y: 95.3}
]
const testChart = new Chart(ctx, {
    type: "line",
    data: data,
    options: {
        onClick: (e) => {
            const canvasPos = getRelativePosition(e, testChart)

            const dataX = chart.scales.x.getValueForPixel(canvasPos.x)
            const dataY = chart.scales.y.getValueForPixel(canvasPos.y)

            // Make not intrusive (Use text in ui instead of popup)
            alert(`In ${dataX} minutes of training the model had a ${dataY}% success rate`)
        }
    }
})