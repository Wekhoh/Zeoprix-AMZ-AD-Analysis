import axios from "axios";
import { message } from "antd";

const api = axios.create({
	baseURL: "/api",
	timeout: 30000,
});

// Request interceptor: common headers
api.interceptors.request.use((config) => {
	config.headers.set("Accept", "application/json");
	return config;
});

// Response interceptor: surface non-200 errors
api.interceptors.response.use(
	(response) => response,
	(error: unknown) => {
		if (axios.isAxiosError(error)) {
			const status = error.response?.status;
			const detail =
				(error.response?.data as { detail?: string } | undefined)?.detail ??
				error.message;

			if (status === 422) {
				void message.error(`请求参数有误: ${detail}`);
			} else if (status === 404) {
				void message.error("请求的资源不存在");
			} else if (status && status >= 500) {
				void message.error(`服务器错误 (${status}): ${detail}`);
			} else if (status) {
				void message.error(`请求失败 (${status}): ${detail}`);
			} else {
				void message.error(`网络错误: ${error.message}`);
			}
		}
		return Promise.reject(error);
	},
);

export default api;
