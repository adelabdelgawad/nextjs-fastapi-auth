"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { login } from "@/lib/session"; // Assume this is your login function
import Image from "next/image";

type FormValues = {
  username: string;
  password: string;
};

export function LoginForm() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>();

  /**
   * Handles form submission, sending login data to the server.
   * @param data - The username and password entered by the user.
   */
  const onSubmit = async (data: FormValues) => {
    setLoading(true);
    setError(null);
  
    try {
      // Convert data object into FormData
      const formData = new FormData();
      formData.append("username", data.username);
      formData.append("password", data.password);
  
      const result = await login(formData); // Ensure login receives FormData
      if (result.success) {
        router.push("/");
      } else {
        setError(result.errors?.general || "Invalid credentials.");
      }
    } catch (err) {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-800">
      <div className="w-full max-w-md p-8 m-auto bg-white rounded-2xl shadow-md dark:bg-gray-800">
        <div className="flex items-center justify-center">
        <Image src="/logo.png" alt="MyApp Logo" width={210} height={40} />
        </div>
        <p className="text-center text-gray-500 dark:text-gray-400 pt-4">
          Please login to your account.
        </p>
        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-6">
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              type="text"
              placeholder="Enter your username"
              {...register("username", { required: "Username is required" })}
            />
            {errors.username && (
              <p className="text-red-500 text-sm">{errors.username.message}</p>
            )}
          </div>
          <div className="relative space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Password</Label>
            </div>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              {...register("password", { required: "Password is required" })}
            />
            {errors.password && (
              <p className="text-red-500 text-sm">{errors.password.message}</p>
            )}
          </div>
          {error && <p className="text-red-500 text-sm text-center">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </Button>
        </form>
      </div>
    </div>
  );
}