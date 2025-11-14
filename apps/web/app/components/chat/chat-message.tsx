import { cn } from "~/lib/utils";
import { type UIMessage } from "~/lib/api-client";
import { formatAssistantMessage, formatUserMessage } from "~/lib/markdown";
import { AddressForm } from "./address-form";

interface AddressData {
  street: string;
  exteriorNumber?: string;
  interiorNumber?: string;
  neighborhood: string;
  postalCode: string;
  municipality: string;
  state: string;
}

interface ChatMessageProps {
  message: UIMessage;
  onSendMessage?: (message: string) => void;
}

export function ChatMessage({ message, onSendMessage }: ChatMessageProps) {
  const isUser = message.sender === 'user';

  const handleAddressSubmit = async (addressData: AddressData) => {
    if (!onSendMessage) return;
    
    const addressMessage = `Mi domicilio fiscal es:
Calle: ${addressData.street}${addressData.exteriorNumber ? ` #${addressData.exteriorNumber}` : ''}${addressData.interiorNumber ? ` Int. ${addressData.interiorNumber}` : ''}
Colonia: ${addressData.neighborhood}
Código Postal: ${addressData.postalCode}
Municipio: ${addressData.municipality}
Estado: ${addressData.state}`;

    onSendMessage(addressMessage);
  };

  return (
    <div className={cn(
      "flex",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div
        className={cn(
          "px-5 py-4 rounded-2xl shadow-lg",
          isUser
            ? "max-w-xs lg:max-w-md bg-sky-600 text-white"
            : message.showAddressForm 
            ? "max-w-full w-full" // Full width for address form
            : "max-w-lg lg:max-w-2xl backdrop-blur-md bg-white/80 border border-white/50 text-sky-700"
        )}
      >
        {isUser ? (
          formatUserMessage(message.content)
        ) : message.showAddressForm ? (
          <div className="space-y-4">
            {/* Show the agent's message first */}
            <div className="backdrop-blur-md bg-white/80 border border-white/50 text-sky-700 px-5 py-4 rounded-2xl">
              {formatAssistantMessage(message.content)}
            </div>
            {/* Then show the address form */}
            <AddressForm 
              onAddressSubmit={handleAddressSubmit}
            />
          </div>
        ) : (
          formatAssistantMessage(message.content)
        )}
      </div>
    </div>
  );
}