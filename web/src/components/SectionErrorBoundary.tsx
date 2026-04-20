import { Component } from 'react'
import type { ReactNode, ErrorInfo } from 'react'
import { Card } from './Card'

interface Props {
  name: string
  children: ReactNode
}

interface State {
  error: Error | null
}

export class SectionErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(`${this.props.name} crash:`, error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <Card title={this.props.name}>
          <div className="text-accent-red text-[13px]">Failed to render: {this.state.error.message}</div>
        </Card>
      )
    }
    return this.props.children
  }
}
