import { AuthForm } from "@/components/auth-form"

export default function RegisterPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-16">
      <p className="mb-8 text-sm font-medium tracking-tight">Doc QA</p>
      <AuthForm mode="register" />
    </main>
  )
}
