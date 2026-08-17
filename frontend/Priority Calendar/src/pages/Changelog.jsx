import Nav from '../components/Nav';
import './Changelog.css';

const entries = [
  {
    tag: 'The Overhaul Update',
    date: 'August 17, 2026',
    items: [
      "Added visual quality updates to several app features.",
      "Provided bonus clarification for Canvas Imports regarding the class an assignment belongs to.",
      "Fixed issues with Shepherd prompts creating whitespace.",
      "Limited year context range for adding assignments and viewing dates on the Calendar.",
      "Ensured that date parsing is aware of Daylight Savings Time during Canvas sync and app logic.",
      "Added a 24-hour cooldown to swapping Canvas iCalendar links and Canvas Access Tokens.",
      "Fixed the log-in button on non-landing pages redirecting to the landing page.",
      "Added a log-in screen during and after completing OAuth but before the page is loaded in.",
      "Added alternate color palettes to the Dashboard.",
      "Improved design to be Mobile-friendly.",
      "Added the ability to add repeating tasks/events.",
    ],
  },
  
  {
    tag: 'The (Small) Launch Update',
    date: 'March 31, 2026',
    items: [
      "Talk about a Happy Birthday present: an app for some people to try out and help me develop.",
      "Feel free to experiment around with features and provide feedback either through Discord or email, whichever you prefer and contact me from.",
      'Did a weird dance, twice.',
    ],
  },
];

export default function Changelog() {
  return (
    <div className="changelog">
      <Nav />
      <main className="changelog-content">
        <a href="https://github.com/ImTheFireKing/PriorityCalendar" className="changelog-github" target="_blank" rel="noreferrer">View on GitHub →</a>
        {entries.map((entry, i) => (
          <div className="changelog-entry" key={i}>
            <span className="changelog-tag">{entry.tag}</span>
            <h1 className="changelog-date">{entry.date} Changelog</h1>
            <ul className="changelog-list">
              {entry.items.map((item, j) => (
                <li key={j}>{item}</li>
              ))}
            </ul>
          </div>
        ))}
      </main>
    </div>
  );
}