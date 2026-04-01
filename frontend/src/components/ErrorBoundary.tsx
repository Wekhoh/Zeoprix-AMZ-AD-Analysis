import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { Result, Button } from "antd";

interface Props {
	children: ReactNode;
}

interface State {
	hasError: boolean;
	error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
	constructor(props: Props) {
		super(props);
		this.state = { hasError: false, error: null };
	}

	static getDerivedStateFromError(error: Error): State {
		return { hasError: true, error };
	}

	componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
		// eslint-disable-next-line no-console
		console.error("[ErrorBoundary]", error, errorInfo);
	}

	handleReload = (): void => {
		window.location.reload();
	};

	render(): ReactNode {
		if (this.state.hasError) {
			const isDev = import.meta.env.DEV;
			return (
				<div
					style={{
						display: "flex",
						alignItems: "center",
						justifyContent: "center",
						minHeight: "100vh",
						padding: 24,
					}}
				>
					<Result
						status="error"
						title="页面出错了"
						subTitle={
							isDev && this.state.error
								? this.state.error.message
								: "抱歉，页面遇到了一些问题。请尝试刷新页面。"
						}
						extra={
							<Button type="primary" onClick={this.handleReload}>
								刷新页面
							</Button>
						}
					/>
				</div>
			);
		}

		return this.props.children;
	}
}
