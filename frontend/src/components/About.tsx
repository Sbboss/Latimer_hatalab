import { ArrowRight } from "./Icons";

type Props = {
  onStart: () => void;
};

export function About({ onStart }: Props) {
  return (
    <section className="about" id="about" aria-labelledby="about-title">
      <div className="container about-grid">
        <div className="about-intro">
          <p className="about-kicker">Our purpose</p>
          <h1 id="about-title">Better words are only the beginning.</h1>
          <p className="about-lede">
            Bias Intelligence helps people understand the assumptions behind
            language, connect them to decades of social research, and carry
            that understanding into life beyond the screen.
          </p>
          <button className="btn btn-accent" onClick={onStart}>
            Start analysis <ArrowRight size={16} />
          </button>
        </div>

        <div className="about-principles">
          <article>
            <h2>Learn before rewriting</h2>
            <p>
              A polished sentence can hide unchanged assumptions. Each signal
              explains the pattern, invites reflection, and then offers a
              concrete revision.
            </p>
          </article>
          <article>
            <h2>Use evidence with boundaries</h2>
            <p>
              GSS and ISSP questions add historical and social context. Source
              wording, coverage, and limits stay visible so evidence supports
              interpretation without pretending to settle it.
            </p>
          </article>
          <article>
            <h2>Keep judgment human</h2>
            <p>
              Automated analysis can surface a question. People remain responsible for moral
              judgment, deeper understanding, and how they act toward one
              another.
            </p>
          </article>
        </div>
      </div>

      <div className="container about-lab">
        <div>
          <p className="about-kicker">Humanity and Technoscience Lab</p>
          <h2>Research shaped around people, difference, and technology.</h2>
        </div>
        <div>
          <p>
            This project reflects the core philosophy of Rayvon Fouché and
            Northwestern University’s Humanity and Technoscience (HAT) Lab:
            technology should deepen understanding of difference and bias while
            preserving human agency.
          </p>
          <a className="about-email" href="mailto:fouche@northwestern.edu">
            Contact Rayvon Fouché
            <span>fouche@northwestern.edu</span>
          </a>
        </div>
      </div>
    </section>
  );
}
