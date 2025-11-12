import React from 'react';

interface MarkdownElement {
  type: 'text' | 'bold' | 'list' | 'paragraph';
  content: string;
  children?: MarkdownElement[];
}

export function parseMarkdown(text: string): React.ReactNode[] {
  // Split text into paragraphs
  const paragraphs = text.split('\n\n').filter(p => p.trim());
  
  return paragraphs.map((paragraph, index) => {
    const trimmed = paragraph.trim();
    
    // Check if it's a numbered list
    if (isNumberedList(trimmed)) {
      return renderNumberedList(trimmed, index);
    }
    
    // Regular paragraph with formatting
    return renderParagraph(trimmed, index);
  });
}

function isNumberedList(text: string): boolean {
  const lines = text.split('\n');
  return lines.length > 1 && lines.some(line => /^\d+\.\s/.test(line.trim()));
}

function renderNumberedList(text: string, key: number): React.ReactNode {
  const lines = text.split('\n').map(line => line.trim()).filter(Boolean);
  
  return (
    <div key={key} className="space-y-3 my-3">
      {lines.map((line, lineIndex) => {
        const numberMatch = line.match(/^(\d+)\.\s(.+)/);
        if (numberMatch) {
          const [, number, content] = numberMatch;
          return (
            <div key={lineIndex} className="flex gap-3 items-start">
              <span className="shrink-0 w-7 h-7 bg-linear-to-br from-sky-100 to-sky-200 text-sky-700 rounded-full flex items-center justify-center text-sm font-bold shadow-sm border border-sky-200">
                {number}
              </span>
              <div className="flex-1 pt-1">
                {renderInlineFormatting(content)}
              </div>
            </div>
          );
        }
        return (
          <div key={lineIndex} className="ml-10 text-sky-600 leading-relaxed">
            {renderInlineFormatting(line)}
          </div>
        );
      })}
    </div>
  );
}

function renderParagraph(text: string, key: number): React.ReactNode {
  return (
    <p key={key} className="mb-4 last:mb-0 leading-relaxed text-sky-700">
      {renderInlineFormatting(text)}
    </p>
  );
}

function renderInlineFormatting(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let currentIndex = 0;
  
  // Find all **bold** patterns
  const boldRegex = /\*\*(.+?)\*\*/g;
  let match;
  
  while ((match = boldRegex.exec(text)) !== null) {
    // Add text before the bold part
    if (match.index > currentIndex) {
      parts.push(text.slice(currentIndex, match.index));
    }
    
    // Add bold text with better styling
    parts.push(
      <strong key={`bold-${match.index}`} className="font-bold text-sky-800">
        {match[1]}
      </strong>
    );
    
    currentIndex = match.index + match[0].length;
  }
  
  // Add remaining text
  if (currentIndex < text.length) {
    parts.push(text.slice(currentIndex));
  }
  
  return parts.length ? parts : [text];
}

export function formatAssistantMessage(content: string): React.ReactNode {
  return (
    <div className="text-sky-700 leading-relaxed">
      {parseMarkdown(content)}
    </div>
  );
}

export function formatUserMessage(content: string): React.ReactNode {
  // For user messages, keep simple formatting
  return (
    <div className="whitespace-pre-wrap">
      {content}
    </div>
  );
}