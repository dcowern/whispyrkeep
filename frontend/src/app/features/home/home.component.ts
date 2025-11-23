import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  LucideAngularModule,
  Shield,
  Sparkles,
  Swords,
  Users,
  Globe,
  BookOpen,
  Wand2,
  ChevronRight
} from 'lucide-angular';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [RouterLink, LucideAngularModule],
  template: `
    <main id="main-content" class="home">
      <!-- Animated background orbs -->
      <div class="home__bg-orb home__bg-orb--1"></div>
      <div class="home__bg-orb home__bg-orb--2"></div>
      <div class="home__bg-orb home__bg-orb--3"></div>

      <!-- Hero Section -->
      <section class="hero">
        <div class="hero__badge animate-fade-in-down">
          <lucide-icon [img]="SparklesIcon" />
          AI-Powered Adventures
        </div>

        <h1 class="hero__title animate-fade-in">
          <span class="hero__title-line">Your Story.</span>
          <span class="hero__title-line hero__title-line--accent">Your Rules.</span>
        </h1>

        <p class="hero__subtitle animate-fade-in-up">
          Experience immersive single-player RPG adventures powered by AI.
          Create characters, build worlds, and let the story unfold.
        </p>

        <nav class="hero__nav animate-fade-in-up" style="animation-delay: 200ms">
          <a routerLink="/auth/register" class="btn btn--primary btn--lg">
            <lucide-icon [img]="Wand2Icon" />
            Start Your Adventure
            <lucide-icon [img]="ChevronRightIcon" />
          </a>
          <a routerLink="/auth/login" class="btn btn--lg">
            Sign In
          </a>
        </nav>
      </section>

      <!-- Features Section -->
      <section class="features">
        <div class="feature-card animate-fade-in-up" style="animation-delay: 300ms">
          <div class="feature-card__icon">
            <lucide-icon [img]="SwordsIcon" />
          </div>
          <h3 class="feature-card__title">Epic Campaigns</h3>
          <p class="feature-card__description">
            Embark on AI-driven adventures with SRD 5.2 mechanics. Every choice matters.
          </p>
        </div>

        <div class="feature-card animate-fade-in-up" style="animation-delay: 400ms">
          <div class="feature-card__icon feature-card__icon--secondary">
            <lucide-icon [img]="UsersIcon" />
          </div>
          <h3 class="feature-card__title">Unique Characters</h3>
          <p class="feature-card__description">
            Build heroes with depth. Full character creation with races, classes, and backgrounds.
          </p>
        </div>

        <div class="feature-card animate-fade-in-up" style="animation-delay: 500ms">
          <div class="feature-card__icon feature-card__icon--accent">
            <lucide-icon [img]="GlobeIcon" />
          </div>
          <h3 class="feature-card__title">Custom Universes</h3>
          <p class="feature-card__description">
            Create your own worlds with custom lore, or explore pre-built settings.
          </p>
        </div>

        <div class="feature-card animate-fade-in-up" style="animation-delay: 600ms">
          <div class="feature-card__icon feature-card__icon--info">
            <lucide-icon [img]="BookOpenIcon" />
          </div>
          <h3 class="feature-card__title">Persistent Stories</h3>
          <p class="feature-card__description">
            Your adventures are saved. Return anytime to continue your journey.
          </p>
        </div>
      </section>

      <!-- Footer -->
      <footer class="home__footer animate-fade-in" style="animation-delay: 700ms">
        <div class="home__logo">
          <lucide-icon [img]="ShieldIcon" />
          <span>WhispyrKeep</span>
        </div>
      </footer>
    </main>
  `,
  styles: [`
    .home {
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: var(--wk-space-8);
      position: relative;
      overflow: hidden;
    }

    /* Animated background orbs */
    .home__bg-orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(120px);
      opacity: 0.25;
      pointer-events: none;
      animation: float 25s ease-in-out infinite;
    }

    .home__bg-orb--1 {
      width: 700px;
      height: 700px;
      background: var(--wk-primary);
      top: -300px;
      right: -200px;
    }

    .home__bg-orb--2 {
      width: 600px;
      height: 600px;
      background: var(--wk-secondary);
      bottom: -200px;
      left: -200px;
      animation-delay: -8s;
    }

    .home__bg-orb--3 {
      width: 400px;
      height: 400px;
      background: var(--wk-accent);
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      animation-delay: -15s;
      opacity: 0.15;
    }

    @keyframes float {
      0%, 100% {
        transform: translate(0, 0) scale(1);
      }
      25% {
        transform: translate(30px, -40px) scale(1.05);
      }
      50% {
        transform: translate(-20px, 30px) scale(0.95);
      }
      75% {
        transform: translate(-40px, -20px) scale(1.02);
      }
    }

    /* Hero Section */
    .hero {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      padding: var(--wk-space-16) 0;
      max-width: 800px;
      position: relative;
      z-index: 1;
    }

    .hero__badge {
      display: inline-flex;
      align-items: center;
      gap: var(--wk-space-2);
      padding: var(--wk-space-2) var(--wk-space-4);
      background: var(--wk-primary-glow);
      border: 1px solid var(--wk-primary);
      border-radius: var(--wk-radius-full);
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      color: var(--wk-primary-light);
      margin-bottom: var(--wk-space-6);
      opacity: 0;

      lucide-icon {
        width: 16px;
        height: 16px;
      }
    }

    .hero__title {
      font-size: clamp(2.5rem, 8vw, 4.5rem);
      font-weight: var(--wk-font-bold);
      line-height: 1.1;
      margin: 0 0 var(--wk-space-6);
      opacity: 0;
    }

    .hero__title-line {
      display: block;
      color: var(--wk-text-primary);
    }

    .hero__title-line--accent {
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-accent) 50%, var(--wk-secondary) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .hero__subtitle {
      font-size: var(--wk-text-lg);
      color: var(--wk-text-secondary);
      max-width: 600px;
      margin: 0 0 var(--wk-space-8);
      line-height: var(--wk-leading-relaxed);
      opacity: 0;
    }

    .hero__nav {
      display: flex;
      gap: var(--wk-space-4);
      flex-wrap: wrap;
      justify-content: center;
      opacity: 0;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: var(--wk-space-2);
      padding: var(--wk-space-3) var(--wk-space-6);
      border-radius: var(--wk-radius-lg);
      text-decoration: none;
      font-weight: var(--wk-font-medium);
      font-size: var(--wk-text-sm);
      border: 1px solid var(--wk-glass-border);
      color: var(--wk-text-primary);
      background: var(--wk-glass-bg-light);
      backdrop-filter: blur(var(--wk-blur-sm));
      cursor: pointer;
      transition:
        background var(--wk-transition-fast),
        border-color var(--wk-transition-fast),
        box-shadow var(--wk-transition-fast),
        transform var(--wk-transition-fast);

      lucide-icon {
        width: 18px;
        height: 18px;
      }

      &:hover {
        background: var(--wk-surface-hover);
        border-color: var(--wk-glass-border-hover);
        transform: translateY(-2px);
      }

      &--primary {
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
        border-color: var(--wk-primary);
        color: white;
        box-shadow: 0 0 30px var(--wk-primary-glow);

        &:hover {
          background: linear-gradient(135deg, var(--wk-primary-light) 0%, var(--wk-primary) 100%);
          box-shadow: var(--wk-shadow-glow-primary), var(--wk-shadow-lg);
        }
      }

      &--lg {
        padding: var(--wk-space-4) var(--wk-space-8);
        font-size: var(--wk-text-base);
        border-radius: var(--wk-radius-xl);

        lucide-icon {
          width: 20px;
          height: 20px;
        }
      }
    }

    /* Features Section */
    .features {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: var(--wk-space-6);
      max-width: 1000px;
      width: 100%;
      padding: var(--wk-space-8) 0;
      position: relative;
      z-index: 1;
    }

    .feature-card {
      position: relative;
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      -webkit-backdrop-filter: blur(var(--wk-blur-md));
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      padding: var(--wk-space-6);
      text-align: center;
      opacity: 0;
      transition:
        border-color var(--wk-transition-fast),
        box-shadow var(--wk-transition-smooth),
        transform var(--wk-transition-smooth);

      /* Glass shine */
      &::before {
        content: '';
        position: absolute;
        inset: 0;
        background: var(--wk-glass-shine);
        border-radius: inherit;
        pointer-events: none;
      }

      &:hover {
        border-color: var(--wk-primary);
        box-shadow: 0 0 30px var(--wk-primary-glow);
        transform: translateY(-4px);
      }
    }

    .feature-card__icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 56px;
      height: 56px;
      margin: 0 auto var(--wk-space-4);
      background: var(--wk-primary-glow);
      border-radius: var(--wk-radius-xl);
      color: var(--wk-primary);

      lucide-icon {
        width: 28px;
        height: 28px;
      }

      &--secondary {
        background: var(--wk-secondary-glow);
        color: var(--wk-secondary);
      }

      &--accent {
        background: var(--wk-accent-glow);
        color: var(--wk-accent);
      }

      &--info {
        background: var(--wk-info-glow);
        color: var(--wk-info);
      }
    }

    .feature-card__title {
      font-size: var(--wk-text-lg);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
      margin: 0 0 var(--wk-space-2);
    }

    .feature-card__description {
      font-size: var(--wk-text-sm);
      color: var(--wk-text-secondary);
      margin: 0;
      line-height: var(--wk-leading-relaxed);
    }

    /* Footer */
    .home__footer {
      margin-top: auto;
      padding-top: var(--wk-space-8);
      opacity: 0;
    }

    .home__logo {
      display: flex;
      align-items: center;
      gap: var(--wk-space-2);
      color: var(--wk-text-muted);
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);

      lucide-icon {
        width: 20px;
        height: 20px;
        color: var(--wk-primary);
      }
    }
  `]
})
export class HomeComponent {
  // Lucide icons
  readonly ShieldIcon = Shield;
  readonly SparklesIcon = Sparkles;
  readonly SwordsIcon = Swords;
  readonly UsersIcon = Users;
  readonly GlobeIcon = Globe;
  readonly BookOpenIcon = BookOpen;
  readonly Wand2Icon = Wand2;
  readonly ChevronRightIcon = ChevronRight;
}
