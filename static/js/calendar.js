document.addEventListener('DOMContentLoaded', function() {
    // Get current date
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth();
    const currentYear = currentDate.getFullYear();
    const today = {
        date: currentDate.getDate(),
        month: currentMonth,
        year: currentYear
    }; // Store today's date, month, and year

    // Render calendar
    renderCalendar(currentMonth, currentYear, today);

    // Navigation buttons
    document.querySelector('.prev-month').addEventListener('click', function() {
        const currentMonthElement = document.querySelector('.calendar-month');
        const [monthName, year] = currentMonthElement.textContent.split(' ');
        const monthIndex = new Date(`${monthName} 1, ${year}`).getMonth();
        let newMonth = monthIndex - 1;
        let newYear = parseInt(year);

        if (newMonth < 0) {
            newMonth = 11;
            newYear -= 1;
        }

        renderCalendar(newMonth, newYear, today);
    });

    document.querySelector('.next-month').addEventListener('click', function() {
        const currentMonthElement = document.querySelector('.calendar-month');
        const [monthName, year] = currentMonthElement.textContent.split(' ');
        const monthIndex = new Date(`${monthName} 1, ${year}`).getMonth();
        let newMonth = monthIndex + 1;
        let newYear = parseInt(year);

        if (newMonth > 11) {
            newMonth = 0;
            newYear += 1;
        }

        renderCalendar(newMonth, newYear, today);
    });
});

function renderCalendar(month, year, today) {
    const monthNames = ["January", "February", "March", "April", "May", "June",
                        "July", "August", "September", "October", "November", "December"];
    
    // Set month and year header
    document.querySelector('.calendar-month').textContent = `${monthNames[month]} ${year}`;
    
    // Get first day of month and total days in month
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    // Clear previous days
    const daysContainer = document.querySelector('.calendar-days');
    daysContainer.innerHTML = '';
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day empty';
        daysContainer.appendChild(emptyDay);
    }
    
    // Add cells for each day of the month
    for (let day = 1; day <= daysInMonth; day++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        dayElement.textContent = day;
        
        // Highlight current day
        if (day === today.date && month === today.month && year === today.year) {
            dayElement.classList.add('today');
        }
        
        daysContainer.appendChild(dayElement);
    }
}