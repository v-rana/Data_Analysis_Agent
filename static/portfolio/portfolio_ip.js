(() => {
  "use strict";

  const ipButton = document.getElementById("ip-button");
  const ipResult = document.getElementById("result");

  async function getIP() {
    if (!ipButton || !ipResult) {
      return;
    }

    ipButton.disabled = true;
    ipButton.textContent = "CHECKING...";

    try {
      const response = await fetch("/ip");

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const data = await response.json();
      ipResult.textContent = `Your IP: ${data.ip}`;
      ipButton.textContent = "HIDE IP";
      ipButton.dataset.visible = "true";
    } catch (error) {
      console.error("API request failed:", error);
      ipResult.textContent = "IP unavailable";
      ipButton.textContent = "TRY AGAIN";
    } finally {
      ipButton.disabled = false;
    }
  }

  ipButton?.addEventListener("click", () => {
    if (ipButton.dataset.visible === "true") {
      ipResult.textContent = "";
      ipButton.textContent = "SHOW IP";
      delete ipButton.dataset.visible;
      return;
    }

    getIP();
  });
})();
