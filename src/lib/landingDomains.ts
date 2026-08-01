export interface LandingDomain {
  name: string;
  color: string;
  icon: string;
  blurb: string;
  sample: string;
  duration: string;
}

// Colors match the DOMAIN_COLORS convention used across dashboard/recommendation views.
export const LANDING_DOMAINS: LandingDomain[] = [
  {
    name: "Creativity",
    color: "#C97A3D",
    icon: "🎨",
    blurb: "Ideas made tangible — visual art, music, and making.",
    sample: "A 12-minute short on kinetic sculpture, picked to unstick your current project.",
    duration: "12 min · Film",
  },
  {
    name: "Mindset",
    color: "#6E5AA0",
    icon: "🧠",
    blurb: "Reframe how you think before you change what you do.",
    sample: "A podcast on cognitive reframing techniques used by elite athletes.",
    duration: "24 min · Podcast",
  },
  {
    name: "Health",
    color: "#5E8F5A",
    icon: "🌿",
    blurb: "Small physical resets that compound.",
    sample: "A 7-minute breathwork sequence shown to lower pre-sleep cortisol.",
    duration: "7 min · Audio",
  },
  {
    name: "Knowledge",
    color: "#3E5E8C",
    icon: "📚",
    blurb: "Curiosity, pointed somewhere useful.",
    sample: "An essay on how constraint breeds better decisions — matched to your goal.",
    duration: "9 min · Read",
  },
  {
    name: "Career",
    color: "#9C7A3A",
    icon: "💼",
    blurb: "Momentum in the work that pays the bills.",
    sample: "A case study on negotiating scope before salary, timed to your next review.",
    duration: "11 min · Read",
  },
  {
    name: "Relationships",
    color: "#A8497A",
    icon: "🤝",
    blurb: "The people you're becoming this for.",
    sample: "A 10-minute film on repairing after conflict, without over-apologizing.",
    duration: "10 min · Film",
  },
  {
    name: "Finance",
    color: "#7A8C4A",
    icon: "💰",
    blurb: "Decisions your future self will thank you for.",
    sample: "An animated explainer on compounding, sized to your actual numbers.",
    duration: "6 min · Animation",
  },
  {
    name: "Purpose",
    color: "#2F6F6B",
    icon: "🧭",
    blurb: "Why any of the above matters.",
    sample: "An interview on defining \"enough,\" queued for your quietest hour today.",
    duration: "18 min · Podcast",
  },
];
