
document.addEventListener("DOMNodeInserted", function (event) {
                if (event.target.className && event.target.className.startsWith("form-")) {
                        h = event.target.querySelector('.help-block')
                    if (h) {
                       urlpat = /(\b(https?):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/gim;
                       h.innerHTML = h.innerHTML.replace(urlpat, '<a href="$1" target="_blank">here</a>');
                    }
                }
            }, false);
