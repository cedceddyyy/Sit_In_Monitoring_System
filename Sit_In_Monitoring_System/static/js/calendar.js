document.addEventListener("DOMContentLoaded", function () {
    const calendarContainer = document.createElement("div");
    calendarContainer.className = "calendar";
    document.body.appendChild(calendarContainer);

    function renderCalendar() {
        const date = new Date();
        const month = date.getMonth();
        const year = date.getFullYear();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        calendarContainer.innerHTML = ""; // Clear previous content

        const monthYearHeader = document.createElement("h2");
        monthYearHeader.textContent = date.toLocaleString('default', { month: 'long' }) + " " + year;
        calendarContainer.appendChild(monthYearHeader);

        const daysGrid = document.createElement("div");
        daysGrid.className = "days-grid";

        for (let day = 1; day <= daysInMonth; day++) {
            const dayElement = document.createElement("div");
            dayElement.className = "day";
            dayElement.textContent = day;
            daysGrid.appendChild(dayElement);
        }

        calendarContainer.appendChild(daysGrid);
    }

    renderCalendar();
});