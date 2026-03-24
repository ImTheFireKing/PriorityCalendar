import Nav from '../components/Nav';
import './Changelog.css';

const entries = [
  {
    tag: 'The Launch Update',
    date: 'March 13, 2026',
    items: [
      "WE'RE LIVE BABY!",
      "Launched a website that'll help who knows how many college students take control of their academic lives.",
      "Pushed Google Calendar into Pseudo Retirement for tracking college assignments and projects",
      'Did a happy dance, twice.',
    ],
  },
];

export default function Changelog() {
  return (
    <div className="changelog">
      <Nav />
      <main className="changelog-content">
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