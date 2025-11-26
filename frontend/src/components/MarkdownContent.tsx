import ReactMarkdown from 'react-markdown'
import { Box, BoxProps } from '@mui/material'

interface MarkdownContentProps extends BoxProps {
  children: string
}

export default function MarkdownContent({ children, sx, ...props }: MarkdownContentProps) {
  return (
    <Box
      sx={{
        '& p': { margin: '0.5em 0' },
        '& h1, & h2, & h3, & h4, & h5, & h6': { 
          margin: '1em 0 0.5em',
          fontWeight: 600,
        },
        '& h1': { fontSize: '2em' },
        '& h2': { fontSize: '1.5em' },
        '& h3': { fontSize: '1.25em' },
        '& ul, & ol': { 
          paddingLeft: '1.5em',
          margin: '0.5em 0',
        },
        '& li': { margin: '0.25em 0' },
        '& code': {
          bgcolor: 'grey.100',
          padding: '0.2em 0.4em',
          borderRadius: '3px',
          fontFamily: 'monospace',
          fontSize: '0.9em',
        },
        '& pre': {
          bgcolor: 'grey.100',
          padding: '1em',
          borderRadius: '4px',
          overflow: 'auto',
          '& code': {
            bgcolor: 'transparent',
            padding: 0,
          },
        },
        '& blockquote': {
          borderLeft: '4px solid',
          borderColor: 'primary.main',
          paddingLeft: '1em',
          margin: '1em 0',
          color: 'text.secondary',
        },
        '& strong': { fontWeight: 600 },
        '& em': { fontStyle: 'italic' },
        '& hr': {
          border: 'none',
          borderTop: '1px solid',
          borderColor: 'divider',
          margin: '1em 0',
        },
        ...sx,
      }}
      {...props}
    >
      <ReactMarkdown>{children}</ReactMarkdown>
    </Box>
  )
}
