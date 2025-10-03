export const GREETING_MESSAGES = ["Where shall we go today"];

export function getRandomGreeting(): string {
  return GREETING_MESSAGES[
    Math.floor(Math.random() * GREETING_MESSAGES.length)
  ] as string;
}
