const Formatter = new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
});

export function useFilters() {
    const currency = (value: string) => {
        if(value === "-") return value

        return Formatter.format(parseInt(value))
    }
    const dateFormat = (value: string) => {
        const date = new Date(value);
        if(!!date) {
            return `${date.getDate()}.${date.getMonth()+1}.${date.getFullYear()} ${date.getHours()}:${date.getMinutes()}`
        }
        return value;
    }

    return { currency, dateFormat }
}
