import { useToastContext } from "../components/ui/Toast";

export function useToast() {
  const { push, remove } = useToastContext();
  return {
    toast: push,
    removeToast: remove,
  };
}

export default useToast;

