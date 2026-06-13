import { SITE_URL } from '@/lib/site-config';

type HowToStep = { name: string; text: string };

type Props = {
  name: string;
  description: string;
  steps: HowToStep[];
  path: string;
};

export function HowToJsonLd({ name, description, steps, path }: Props) {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name,
    description,
    url: `${SITE_URL}${path}`,
    step: steps.map((step, index) => ({
      '@type': 'HowToStep',
      position: index + 1,
      name: step.name,
      text: step.text,
    })),
  };

  return (
    <script
      type='application/ld+json'
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}

export function parseHowToStepsFromMarkdown(body: string): HowToStep[] {
  const steps: HowToStep[] = [];
  const lines = body.split('\n');
  for (const line of lines) {
    const match = line.match(/^##\s*Step\s+\d+[:\.]?\s*(.+)$/i);
    if (match) {
      steps.push({ name: match[1].trim(), text: match[1].trim() });
      continue;
    }
    if (steps.length > 0 && line.trim() && !line.startsWith('#')) {
      const last = steps[steps.length - 1];
      last.text = `${last.text} ${line.trim()}`.trim();
    }
  }
  return steps;
}
