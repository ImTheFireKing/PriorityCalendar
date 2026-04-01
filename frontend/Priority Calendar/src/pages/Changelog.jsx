import Nav from '../components/Nav';
import './Changelog.css';

const entries = [
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