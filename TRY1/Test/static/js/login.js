// Animation et interactions pour la page de login
document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector(".login-form");
  const inputs = document.querySelectorAll("input");
  const loginButton = document.querySelector(".login-button");

  // Animation des inputs au focus
  inputs.forEach((input) => {
    input.addEventListener("focus", function () {
      this.parentElement.style.transform = "scale(1.02)";
    });

    input.addEventListener("blur", function () {
      this.parentElement.style.transform = "scale(1)";
    });
  });

  // Validation basique du formulaire
  form.addEventListener("submit", function (e) {
    let isValid = true;
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    // Validation simple
    if (!username) {
      showError("Veuillez entrer un nom d'utilisateur ou email");
      isValid = false;
    }

    if (!password) {
      showError("Veuillez entrer un mot de passe");
      isValid = false;
    }

    if (!isValid) {
      e.preventDefault();
    } else {
      // Animation de chargement
      loginButton.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <span>Connexion en cours...</span>
                </div>
            `;
      loginButton.disabled = true;
    }
  });

  function showError(message) {
    // Supprimer les anciens messages d'erreur
    const existingError = document.querySelector(".error-message");
    if (existingError) {
      existingError.remove();
    }

    // Créer le nouveau message d'erreur
    const errorDiv = document.createElement("div");
    errorDiv.className = "error-message";
    errorDiv.textContent = message;

    // Insérer avant le formulaire
    form.parentNode.insertBefore(errorDiv, form);
  }

  // Effet de particules optionnel pour le fond
  createParticles();
});

// Effet de particules pour le fond (optionnel)
function createParticles() {
  const container = document.querySelector(".container");
  const particlesCount = 20;

  for (let i = 0; i < particlesCount; i++) {
    const particle = document.createElement("div");
    particle.className = "particle";
    particle.style.cssText = `
            position: fixed;
            width: 4px;
            height: 4px;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            top: ${Math.random() * 100}vh;
            left: ${Math.random() * 100}vw;
            animation: float ${15 + Math.random() * 20}s linear infinite;
            z-index: -1;
        `;

    document.body.appendChild(particle);
  }

  // Ajouter l'animation CSS pour les particules
  const style = document.createElement("style");
  style.textContent = `
        @keyframes float {
            0% {
                transform: translateY(100vh) rotate(0deg);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateY(-100vh) rotate(360deg);
                opacity: 0;
            }
        }
    `;
  document.head.appendChild(style);
}
