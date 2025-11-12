import type { Route } from "./+types/home";
import { ChatLayout } from "~/components/chat";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Chat Assistant" },
    { name: "description", content: "Chat with our AI assistant" },
  ];
}

export default function Home() {
  return <ChatLayout />;
}
