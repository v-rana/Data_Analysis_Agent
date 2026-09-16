(() => {
  "use strict";

  /*
   * ============================================================
   * SITE CONTENT
   * ============================================================
   *
   * Edit this section when personalizing the portfolio.
   * You should not need to modify the rendering code below.
   */

  /*
   * ============================================================
   * DOM REFERENCES
   * ============================================================
   */
  const socialLinks =
  document.getElementById("social-links");

  const projectGrid =
    document.getElementById("project-grid");

  const aboutContent =
    document.getElementById("about-content");

  const experienceContent =
    document.getElementById("experience-content");

  const heroTitle =
    document.getElementById("hero-title");

  const heroSubtitle =
    document.querySelector(".hero-subtitle");

  /*
   * ============================================================
   * HERO
   * ============================================================
   */

  function renderHero() {
    if (heroTitle) {
      heroTitle.textContent = siteData.person.name;
    }

    if (heroSubtitle) {
      heroSubtitle.textContent =
        `${siteData.person.title} — ${siteData.person.subtitle}`;
    }

    document.title =
      `${siteData.person.name} — ${siteData.person.title}`;
  }

 function getSocialIcon(icon) {
  const icons = {
    github: `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path fill="currentColor" d="M12 2C6.48 2 2 6.58 2 12.24c0 4.52 2.87 8.36 6.84 9.72.5.1.68-.22.68-.49v-1.72c-2.78.62-3.37-1.2-3.37-1.2-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.63.07-.63 1 .07 1.53 1.06 1.53 1.06.9 1.58 2.36 1.12 2.94.86.09-.67.35-1.12.64-1.38-2.22-.26-4.55-1.14-4.55-5.05 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.27 2.75 1.05A9.2 9.2 0 0 1 12 7.18c.85 0 1.7.12 2.49.36 1.91-1.32 2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.92-2.33 4.78-4.56 5.04.36.32.68.94.68 1.9v2.58c0 .27.18.59.69.49A10.25 10.25 0 0 0 22 12.24C22 6.58 17.52 2 12 2Z"/>
      </svg>
    `,

    linkedin: `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path fill="currentColor" d="M5.5 3.5A2.5 2.5 0 1 1 5.5 8a2.5 2.5 0 0 1 0-4.5ZM3.25 9.5h4.5V21h-4.5V9.5ZM10.25 9.5h4.31v1.57h.06c.6-1.13 2.07-2.32 4.26-2.32 4.56 0 5.4 3 5.4 6.9V21h-4.5v-4.73c0-1.13-.02-2.59-1.58-2.59-1.58 0-1.82 1.23-1.82 2.5V21h-4.5V9.5Z"/>
      </svg>
    `,

    email: `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path fill="currentColor" d="M3 5.5h18A1.5 1.5 0 0 1 22.5 7v10A1.5 1.5 0 0 1 21 18.5H3A1.5 1.5 0 0 1 1.5 17V7A1.5 1.5 0 0 1 3 5.5Zm0 2.25v.43l9 5.62 9-5.62v-.43H3Zm18 8.5V10.85l-8.4 5.25a1.1 1.1 0 0 1-1.2 0L3 10.85v5.4h18Z"/>
      </svg>
    `
  };

  return icons[icon] || "";
}
  function renderSocialLinks() {
  if (!socialLinks) {
    return;
  }

  socialLinks.replaceChildren();

  siteData.socials.forEach((social) => {
    const link =
      document.createElement("a");

    link.className = "social-link";
    link.href = social.url;
    link.target =
      social.url.startsWith("mailto:")
        ? "_self"
        : "_blank";

    if (!social.url.startsWith("mailto:")) {
      link.rel = "noopener noreferrer";
    }

    link.setAttribute(
      "aria-label",
      social.name
    );

    link.dataset.icon = social.icon;

   link.innerHTML = getSocialIcon(social.icon);

    socialLinks.appendChild(link);
  });
}

  /*
   * ============================================================
   * PROJECTS
   * ============================================================
   */

  function createProjectCard(project) {
    const article =
      document.createElement("article");

    article.className = "project-card";

    const header =
      document.createElement("div");

    header.className = "project-card-header";

    const title =
      document.createElement("h2");

    title.textContent = project.name;

    const link =
      document.createElement("a");

    link.className = "project-link";
    link.href = project.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";

    link.setAttribute(
      "aria-label",
      `View ${project.name}`
    );

    link.textContent = "↗";

    header.appendChild(title);
    header.appendChild(link);


    const description =
      document.createElement("p");

    description.className =
      "project-description";

    description.textContent =
      project.description;


    const tags =
      document.createElement("div");

    tags.className = "project-tags";

    tags.setAttribute(
      "aria-label",
      "Technologies"
    );


    project.technologies.forEach(
      (technology) => {
        const tag =
          document.createElement("span");

        tag.textContent = technology;

        tags.appendChild(tag);
      }
    );

    const demoButton = document.createElement(
      project.demoUrl ? "a" : "button"
    );

    demoButton.className = "demo-button";
    demoButton.textContent = "Demo";

    if (project.demoUrl) {
      demoButton.href = project.demoUrl;
      demoButton.setAttribute("aria-label", `Open ${project.name} demo`);
    } else {
      demoButton.type = "button";
      demoButton.setAttribute("aria-label", `${project.name} demo coming soon`);
      demoButton.addEventListener("click", () => {
        window.alert("Coming soon.");
      });
    }

    const actions = document.createElement("div");
    actions.className = "project-actions";
    actions.appendChild(demoButton);

    article.appendChild(header);
    article.appendChild(description);
    article.appendChild(tags);
    article.appendChild(actions);

    return article;
  }


  function renderProjects() {
    if (!projectGrid) {
      return;
    }

    projectGrid.replaceChildren();

    siteData.projects.forEach(
      (project) => {
        const card =
          createProjectCard(project);

        projectGrid.appendChild(card);
      }
    );
  }


  /*
   * ============================================================
   * ABOUT
   * ============================================================
   */

  function renderAbout() {
    if (!aboutContent) {
      return;
    }

    aboutContent.replaceChildren();

    siteData.about.forEach(
      (paragraph) => {
        const element =
          document.createElement("p");

        element.textContent = paragraph;

        aboutContent.appendChild(element);
      }
    );
  }


  /*
   * ============================================================
   * EXPERIENCE
   * ============================================================
   */

  function createExperienceItem(experience) {
    const article =
      document.createElement("article");

    article.className =
      "experience-item";


    const header =
      document.createElement("div");

    header.className =
      "experience-header";


    const role =
      document.createElement("h3");

    role.textContent =
      experience.role;


    const period =
      document.createElement("span");

    period.className =
      "experience-period";

    period.textContent =
      experience.period;


    header.appendChild(role);
    header.appendChild(period);


    const company =
      document.createElement("div");

    company.className =
      "experience-company";

    company.textContent =
      experience.company;


    const description =
      document.createElement("p");

    description.className =
      "experience-description";

    description.textContent =
      experience.description;


    const tags =
      document.createElement("div");

    tags.className = "project-tags";

    if (Array.isArray(experience.skills)) {
      experience.skills.forEach((skill) => {
        const tag =
          document.createElement("span");

        tag.textContent = skill;
        tags.appendChild(tag);
      });
    }


    article.appendChild(header);
    article.appendChild(company);
    article.appendChild(description);
    article.appendChild(tags);

    return article;
  }


  function renderExperience() {
    if (!experienceContent) {
      return;
    }

    experienceContent.replaceChildren();

    siteData.experience.forEach(
      (experience) => {
        const item =
          createExperienceItem(experience);

        experienceContent.appendChild(item);
      }
    );
  }


  /*
   * ============================================================
   * SMOOTH NAVIGATION
   * ============================================================
   */

  const navLinks =
    document.querySelectorAll(
      '.nav-links a[href^="#"]'
    );


  navLinks.forEach((link) => {
    link.addEventListener(
      "click",
      (event) => {
        const targetId =
          link.getAttribute("href");

        const target =
          document.querySelector(targetId);

        if (!target) {
          return;
        }

        event.preventDefault();

        target.scrollIntoView({
          behavior: "smooth",
          block: "start"
        });

        history.pushState(
          null,
          "",
          targetId
        );
      }
    );
  });


  /*
   * ============================================================
   * ACTIVE NAVIGATION
   * ============================================================
   */

  const sections =
    document.querySelectorAll(
      "main section[id]"
    );


  function updateActiveNavigation() {
    const scrollPosition =
      window.scrollY + 120;

    let currentSection = "";

    sections.forEach((section) => {
      const sectionTop =
        section.offsetTop;

      const sectionBottom =
        sectionTop + section.offsetHeight;

      if (
        scrollPosition >= sectionTop &&
        scrollPosition < sectionBottom
      ) {
        currentSection =
          section.id;
      }
    });


    navLinks.forEach((link) => {
      const targetId =
        link.getAttribute("href");

      link.classList.toggle(
        "is-active",
        targetId === `#${currentSection}`
      );
    });
  }


  let ticking = false;


  window.addEventListener(
    "scroll",
    () => {
      if (ticking) {
        return;
      }

      window.requestAnimationFrame(() => {
        updateActiveNavigation();

        ticking = false;
      });

      ticking = true;
    },
    { passive: true }
  );


  /*
   * ============================================================
   * INITIALIZE
   * ============================================================
   */
  renderSocialLinks();
  renderHero();
  renderProjects();
  renderAbout();
  renderExperience();
  updateActiveNavigation();

})();