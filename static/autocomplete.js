document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("city-input");
    const suggestions = document.getElementById("suggestions");

    input.addEventListener("input", function() {
        const query = input.value.trim();

        if (query.length < 2) {
            suggestions.style.display = "none";
            return;
        }

        fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&addressdetails=1&limit=5`)
            .then(response => response.ok ? response : Promise.reject(response))
            .then(response => response.json())
            .then(data => {
                suggestions.innerHTML = "";
                const citySet = new Set();

                data.forEach(place => {
                    const address = place.address;
                    let cityName = address.city || address.town || address.village;
                    if (cityName && !citySet.has(cityName)) {
                        citySet.add(cityName);
                        const li = document.createElement("li");
                        li.textContent = cityName;
                        li.addEventListener("click", function() {
                            input.value = cityName;
                            suggestions.style.display = "none";
                        });
                        suggestions.appendChild(li);
                    }
                });

                if (citySet.size > 0) {
                    suggestions.style.display = "block";
                } else {
                    suggestions.style.display = "none";
                }
            })
            .catch(err => {
                console.error(err);
                suggestions.style.display = "none";
            });
    });

    document.addEventListener("click", function(e) {
        if (e.target !== input) {
            suggestions.style.display = "none";
        }
    });
});
