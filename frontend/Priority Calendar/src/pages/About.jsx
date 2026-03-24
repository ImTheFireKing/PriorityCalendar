import Nav from '../components/Nav';
import './About.css';
import calendarScreenshot from '../assets/pt1.jpg'; 

export default function About() {
  return (
    <div className="about">
      <Nav />
      <main className="about-content">
        <h1 className="about-heading">Why Priority Calendar?</h1>
        <p className="about-body">
          As a college student, I've been: flanked, ganked, swamped, flooded, and utterly violated by
          waves of assignments. To make things worse, when I had the motivation and desire to actually
          get work done, I either didn't know what to work on or — worse — worked on the worst
          assignments I could have possibly started on straight to completion.
        </p>

        {/* 2. Update this wrapper section */}
        <figure className="about-img-wrapper">
          <img 
            src={calendarScreenshot} 
            alt="Me, traumatized from several weeks worth of surprise attacking assignments." 
            className="about-img" 
          />
          <figcaption className="about-caption">
            Several weeks worth of work due across varying classes with differing difficulties sucks. Yet there I was, completely unaware.
          </figcaption>
        </figure>

        <p className="about-body">
          Priority Calendar is the app I wished existed. Rather than just showing you what's due, it
          tells you what to actually work on today — and how much of it — based on deadlines, task
          difficulty, and how your week is structured. It's not a to-do list. It's a daily strategy.
        </p>
      </main>
    </div>
  );
}