type ErrorWithResponse = {
    response?: {
        status?: number
    }
}
export function useProcessResponse() {
    const router = useRouter()

    function processResponse(error: ErrorWithResponse) {
        if (error.response?.status === 403) {
            router.push('/')
        }
        return error
    }

    return { processResponse }
}
