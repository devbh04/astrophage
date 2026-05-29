import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface SensitiveReadingDialogProps {
  open: boolean;
  preview: string;
  onConfirm: () => void;
  onDecline: () => void;
}

export default function SensitiveReadingDialog({
  open,
  preview,
  onConfirm,
  onDecline,
}: SensitiveReadingDialogProps) {
  return (
    <AlertDialog open={open}>
      <AlertDialogContent className="glass-panel wobbly-border border-outline/30 max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="font-headline-md text-xl text-primary flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-solar-gold animate-pulse" />
            Sensitive Reading
          </AlertDialogTitle>
          <AlertDialogDescription className="font-body-md text-on-surface-variant leading-relaxed mt-4">
            This reading touches on a sensitive topic. The cosmos speaks with
            honesty, but we want to make sure you&apos;re ready to receive this
            guidance.
          </AlertDialogDescription>
          {preview && (
            <div className="mt-4 p-4 bg-surface-container wobbly-border-sm">
              <p className="font-annotation-sm text-xs text-solar-gold uppercase tracking-wider mb-2">
                Preview
              </p>
              <p className="font-body-md text-sm text-on-surface-variant italic">
                {preview}
              </p>
            </div>
          )}
        </AlertDialogHeader>
        <AlertDialogFooter className="mt-6">
          <AlertDialogCancel
            onClick={onDecline}
            className="btn-ghost wobbly-border-sm font-nav-label text-nav-label uppercase tracking-widest"
          >
            No, thank you
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="btn-primary wobbly-border-sm font-nav-label text-nav-label uppercase tracking-widest"
          >
            Continue
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
